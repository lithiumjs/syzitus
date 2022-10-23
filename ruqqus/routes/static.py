import time
import jinja2
import pyotp
import pprint
import sass
import mistletoe
from flask import *
import PIL
import io

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.markdown import *
import ruqqus.classes
from ruqqus.classes import *
from ruqqus.mail import *
from ruqqus.__main__ import app, limiter, debug

# take care of misc pages that never really change (much)

@app.route("/assets/style/<board>/<file>.css", methods=["GET"])
@cache.memoize()
def main_css(board, file):

    #print(file, color)

    if file not in ["light", "dark"]:
        abort(404)

    name=f"{app.config['RUQQUSPATH']}/assets/style/{file}.scss"
    #print(name)
    with open(name, "r") as file:
        raw = file.read()

    # This doesn't use python's string formatting because
    # of some odd behavior with css files

    if board=="main":
        scss = raw.replace("{primary}", app.config["COLOR_PRIMARY"])

    else:
        board=get_guild(board)
        scss = raw.replace("{primary}", board.color)

    scss = scss.replace("{secondary}", app.config["COLOR_SECONDARY"])
    scss = scss.replace("{main}", app.config["COLOR_PRIMARY"])

    resp = Response(sass.compile(string=scss), mimetype='text/css')
    resp.headers.add("Cache-Control", "public")
    return resp

@app.get('/assets/images/splash/<width>/<height>')
@cache.memoize()
def get_assets_images_splash(width, height):

    try:
        width=int(width)
        height=int(height)
    except:
        abort(400)

    primary_r=int(app.config["COLOR_PRIMARY"][0:2], 16)
    primary_g=int(app.config["COLOR_PRIMARY"][2:4], 16)
    primary_b=int(app.config["COLOR_PRIMARY"][4:6], 16)

    primary = (primary_r, primary_g, primary_b)

    base = PIL.Image.new("RGBA", (width, height), color=primary)

    font = PIL.ImageFont.load("arial.pil")


    d.text(
        app.config["SITE_NAME"][0:1].lower(), 
        font=font,
        fill=(255,255,255)
        )

    img.rotate(20, expand=True, fillcolor=primary)

    with io.BytesIO() as output:
        img.save(output, format="PNG")
        output.seek(0)
        return send_file(output, mimetype="image/png")




@app.get('/assets/<path:path>')
@limiter.exempt
def static_service(path):

    #try:
    resp = make_response(send_file(safe_join('./assets', path)))
    #except FileNotFoundError:
    #       abort(404)
    resp.headers.add("Cache-Control", "public")

    if request.path.endswith('.css'):
        resp.headers.add("Content-Type", "text/css")
    elif request.path.endswith(".js"):
        resp.headers.add("Content-Type", "text/javascript")
    return resp


@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return send_file("./assets/robots.txt")


@app.route("/slurs.txt", methods=["GET"])
def slurs():
    resp = make_response('\n'.join([x.keyword for x in g.db.query(
        BadWord).order_by(BadWord.keyword.asc()).all()]))
    resp.headers.add("Content-Type", "text/plain")
    return resp


@app.route("/settings", methods=["GET"])
@auth_required
def settings():
    return redirect("/settings/profile")


@app.route("/settings/profile", methods=["GET"])
@auth_required
def settings_profile():
    return render_template("settings_profile.html")


@app.route("/help/titles", methods=["GET"])
@auth_desired
def titles():
    return render_template("/help/titles.html",
                           titles=list(TITLES.values())
                           )


@app.route("/help/terms", methods=["GET"])
@auth_desired
def help_terms():

    cutoff = int(environ.get("tos_cutoff", 0))

    return render_template("/help/terms.html",
                           cutoff=cutoff)


@app.route("/help/badges", methods=["GET"])
@auth_desired
def badges():
    return render_template("help/badges.html",
                           badges=list(BADGE_DEFS.values())
                           )


@app.route("/help/admins", methods=["GET"])
@auth_desired
def help_admins():

    admins = g.db.query(User).filter(
        User.admin_level > 1,
        User.id > 1).order_by(
        User.id.asc()).all()
    admins = [x for x in admins]

    exadmins = g.db.query(User).filter_by(
        admin_level=1).order_by(
        User.id.asc()).all()
    exadmins = [x for x in exadmins]

    return render_template("help/admins.html",
                           admins=admins,
                           exadmins=exadmins
                           )


@app.route("/settings/security", methods=["GET"])
@auth_required
def settings_security():

    mfa_secret=pyotp.random_base32() if not g.user.mfa_secret else None

    if mfa_secret:
        recovery=f"{mfa_secret}+{g.user.id}+{g.user.original_username}"
        recovery=generate_hash(recovery)
        recovery=base36encode(int(recovery,16) % 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        while len(recovery)<25:
            recovery="0"+recovery
        recovery=" ".join([recovery[i:i+5] for i in range(0,len(recovery),5)])
    else:
        recovery=None

    return render_template(
            "settings_security.html",
            mfa_secret=mfa_secret,
            recovery=recovery,
            error=request.args.get("error") or None,
            msg=request.args.get("msg") or None
        )

@app.route("/settings/premium", methods=["GET"])
@auth_required
def settings_premium():
    return render_template("settings_premium.html",
                           error=request.args.get("error") or None,
                           msg=request.args.get("msg") or None
                           )

@app.route("/assets/favicon.ico", methods=["GET"])
def favicon():
    return send_file("./assets/images/logo/favicon.png")


#@app.route("/my_info", methods=["GET"])
#@auth_required
#def my_info():
#    return render_template("my_info.html")


@app.route("/about/<path:path>")
def about_path(path):
    return redirect(f"/help/{path}")


@app.route("/help/<path:path>", methods=["GET"])
@auth_desired
def help_path(path):
    #try:
    to_render=safe_join("help/", f"{path}.html")
    debug(to_render)
    return render_template(to_render)
    #except jinja2.exceptions.TemplateNotFound:
    #    abort(404)


@app.route("/help", methods=["GET"])
@auth_desired
def help_home():
    return render_template("help.html")


@app.route("/help/submit_contact", methods=["POST"])
@is_not_banned
def press_inquiry():

    data = [(x, request.form[x]) for x in request.form if x != "formkey"]
    data.append(("username", g.user.username))
    data.append(("email", g.user.email))

    data = sorted(data, key=lambda x: x[0])

    if request.form.get("press"):
        email_template = "email/press.html"
    else:
        email_template = "email/contactform.html"

    try:
        send_mail(environ.get("admin_email"),
                  "Press Submission",
                  render_template(email_template,
                                  data=data
                                  ),
                  plaintext=str(data)
                  )
    except BaseException:
        return render_template("/help/press.html",
                               error="Unable to save your inquiry. Please try again later.")

    return render_template("/help/press.html",
                           msg="Your inquiry has been saved.")


@app.route("/info/image_hosts", methods=["GET"])
def info_image_hosts():

    sites = g.db.query(Domain).filter_by(
        show_thumbnail=True).order_by(
        Domain.domain.asc()).all()

    sites = [x.domain for x in sites]

    text = "\n".join(sites)

    resp = make_response(text)
    resp.mimetype = "text/plain"
    return resp

@app.route("/dismiss_mobile_tip", methods=["POST"])
def dismiss_mobile_tip():

    session["tooltip_last_dismissed"]=int(time.time())
    session.modified=True

    return "", 204

@app.route("/help/docs")
@cache.memoize(10)
def docs():

    class Doc():

        def __init__(self, **kwargs):
            for entry in kwargs:
                self.__dict__[entry]=kwargs[entry]

        def __str__(self):

            return f"{self.method.upper()} {self.endpoint}\n\n{self.docstring}"

        @property
        def docstring(self):
            return self.target_function.__doc__ if self.target_function.__doc__ else "[doc pending]"

        @property
        def docstring_html(self):
            return mistletoe.markdown(self.docstring)

        @property
        def resource(self):
            return self.endpoint.split('/')[1]

        @property
        def frag(self):
            tail=self.endpoint.replace('/','_')
            tail=tail.replace("<","")
            tail=tail.replace(">","")
            return f"{self.method.lower()}{tail}"
        
        

    docs=[]

    for rule in app.url_map.iter_rules():

        if not rule.rule.startswith("/api/v2/"):
            continue

        endpoint=rule.rule.split("/api/v2")[1]

        for method in rule.methods:
            if method not in ["OPTIONS","HEAD"]:
                break

        new_doc=Doc(
            method=method,
            endpoint=endpoint,
            target_function=app.view_functions[rule.endpoint]
            )

        docs.append(new_doc)

    method_order=["POST", "GET", "PATCH", "PUT", "DELETE"]

    docs.sort(key=lambda x: (x.endpoint, method_order.index(x.method)))

    fulldocs={}

    for doc in docs:
        if doc.resource not in fulldocs:
            fulldocs[doc.resource]=[doc]
        else:
            fulldocs[doc.resource].append(doc)

    return render_template("docs.html", docs=fulldocs, v=None)