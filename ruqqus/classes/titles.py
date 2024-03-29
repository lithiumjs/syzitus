from sqlalchemy import *
from flask import render_template

from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base, cache


class Title():

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def check_eligibility(self, user):

        #legacy compatability function

        return self.evaluate(user)

    @property
    def rendered(self):
        return render_template('title.html', t=self)

    @property
    def json(self):

        return {'id': self.id,
                'text': self.text,
                'color': f'#{self.color}',
                'kind': self.kind
                }

    def evaluate(self, user):

        return bool(self.expr(user))


TITLE_DATA={
    1: {'color': 'aa8855',
        'description': 'Create your first Guild',
        'expr': lambda x: x.boards_created.first(),
        'kind': 1,
        'text': ', Guildmaker'},
    2: {'color': '603abb',
        'description': 'Had a good idea for Ruqqus',
        'expr': lambda x: x.has_badge(15),
        'kind': 1,
        'text': ', the Innovative'},
    3: {'color': '5555dd',
        'description': 'Have at least 10 subscribers',
        'expr': lambda x: x.follower_count>=10,
        'kind': 1,
        'text': ' the Likeable'},
    4: {'color': '5555dd',
        'description': 'Have at least 100 subscribers',
        'expr': lambda x: x.follower_count>=100,
        'kind': 1,
        'text': ' the Popular'},
    5: {'color': '666666',
        'description': 'Responsibly report a security issue to us',
        'expr': lambda x: x.has_badge(4),
        'kind': 3,
        'text': ' the Spymaster'},
    6: {'color': '55aa55',
        'description': "Joined Ruqqus from another user's referral",
        'expr': lambda x: x.referred_by,
        'kind': 4,
        'text': ', the Invited'},
    9: {'color': 'dd5555',
        'description': 'Inadvertently break Ruqqus',
        'expr': lambda x: x.has_badge(7),
        'kind': 3,
        'text': ', Breaker of Ruqqus'},
    11: {'color': '5555dd',
        'description': 'Make a contribution to the Ruqqus codebase',
        'expr': lambda x: x.has_badge(3),
        'kind': 3,
        'text': ' the Codesmith'},
    14: {'color': '5555dd',
        'description': 'Have at least 1 subscriber',
        'expr': lambda x: x.follower_count>=1,
        'kind': 1,
        'text': ' the Friendly'},
    15: {'color': '5555dd',
        'description': 'Have at least 1,000 subscribers',
        'expr': lambda x: x.follower_count>=1000,
        'kind': 1,
        'text': ' the Influential'},
    16: {'color': '5555dd',
        'description': 'Have at least 10,000 subscribers',
        'expr': lambda x: x.follower_count>=10000,
        'kind': 1,
        'text': ', the Famous'},
    20: {'color': '5555dd',
        'description': 'Made a contribution to Ruqqus text or art.',
        'expr': lambda x: x.has_badge(18),
        'kind': 3,
        'text': ' the Artisan'},
    21: {'color': 'dd5555',
        'description': 'Get at least 100 Reputation from a single post.',
        'expr': lambda x: x.submissions.filter(Submission.score_top>=100).count(),
        'kind': 1,
        'text': ' the Hot'},
    23: {'color': '5555dd',
        'description': 'Help test features in development',
        'expr': lambda x: x.has_badge(25),
        'kind': 3,
        'text': ' the Test Dummy'},
    24: {'color': 'aa8855',
        'description': 'A Guild you created grows past 10 members.',
        'expr': lambda x: x.boards_created.filter(Board.stored_subscriber_count>=10).first(),
        'kind': 1,
        'text': ', Guildbuilder'},
    25: {'color': 'aa8855',
        'description': 'A Guild you created grows past 100 members.',
        'expr': lambda x: x.boards_created.filter(Board.stored_subscriber_count>=100).first(),
        'kind': 1,
        'text': ', Guildsmith'},
    26: {'color': 'aa8855',
        'description': 'A Guild you created grows past 1,000 members.',
        'expr': lambda x: x.boards_created.filter(Board.stored_subscriber_count>=1000).first(),
        'kind': 1,
        'text': ', Guildmaster'},
    27: {'color': 'aa8855',
        'description': 'A Guild you created grows past 10,000 members.',
        'expr': lambda x: x.boards_created.filter(Board.stored_subscriber_count>=10000).first(),
        'kind': 1,
        'text': ', Arch Guildmaster'},
    28: {'color': 'aa8855',
        'description': 'A Guild you created grows past 100,000 members.',
        'expr': lambda x: x.boards_created.filter(Board.stored_subscriber_count>=100000).first(),
        'kind': 1,
        'text': ', Guildlord'},
    29: {'color': 'aa8855',
        'description': 'A Guild you created grows past 1,000,000 members.',
        'expr': lambda x: x.boards_created.filter(Board.stored_subscriber_count>=1000000).first(),
        'kind': 1,
        'text': ', Ultimate Guildlord'},
    30: {'color': 'bb00bb',
        'description': 'Refer 1000 friends to join Ruqqus',
        'expr': lambda x: x.referral_count>=1000,
        'kind': 1,
        'text': ', Diamond Recruiter'},
    31: {'color': 'bb00bb',
        'description': 'Refer 1 friend to join Ruqqus.',
        'expr': lambda x: x.referral_count>=1,
        'kind': 1,
        'text': ', Bronze Recruiter'},
    32: {'color': 'bb00bb',
        'description': 'Refer 10 friends to join Ruqqus.',
        'expr': lambda x: x.referral_count>=10,
        'kind': 1,
        'text': ', Silver Recruiter'},
    33: {'color': 'bb00bb',
        'description': 'Refer 100 friends to join Ruqqus.',
        'expr': lambda x: x.referral_count>=100,
        'kind': 1,
        'text': ', Gold Recruiter'}
}

TITLES={x:Title(id=x, **TITLE_DATA[x]) for x in TITLE_DATA}