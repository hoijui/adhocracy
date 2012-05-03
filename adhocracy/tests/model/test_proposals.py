from datetime import timedelta
from datetime import datetime

from adhocracy.tests import TestController
from adhocracy.tests.testtools import (tt_get_instance, tt_make_proposal,
                                       tt_make_str, tt_make_user)

delta = timedelta(minutes=1)
now = datetime.utcnow()
before = now - delta
after = now + delta


class TestProposals(TestController):

    def _make_proposal(self, voting=False):
        creator = tt_make_user('creator')
        proposal = tt_make_proposal(creator=creator, voting=voting)
        return (proposal, creator)

    def _make_norm(self, proposal, creator):
        from adhocracy import model

        instance = tt_get_instance()
        page = model.Page.create(instance,
                                 title=tt_make_str(),
                                 text=tt_make_str(),
                                 creator=creator)
        selection = model.Selection.create(proposal, page, creator)
        selection.variant_poll(page.head)
        return page

    def test_delete_proposal(self):
        (proposal, _) = self._make_proposal()
        proposal.delete(delete_time=now)
        self.assertTrue(proposal.is_deleted())

    def test_delete_proposal_test_delete_time(self):
        (proposal, _) = self._make_proposal()
        proposal.delete(delete_time=now)
        self.assertFalse(proposal.is_deleted(before))
        self.assertTrue(proposal.is_deleted(after))

    def test_delete_deletes_selection_but_leaves_norm(self):
        (proposal, creator) = self._make_proposal()
        norm = self._make_norm(proposal, creator)
        selection = proposal.selections[0]
        self.assertTrue(norm in proposal.children)
        proposal.delete()
        self.assertTrue(proposal.is_deleted())
        self.assertTrue(selection.is_deleted())
        self.assertFalse(norm.is_deleted())

    def test_polls_are_annoyingly_doubled(self):
        '''
        More of a reminder test that delegateable.polls
        is not necessarily a unique list because
        of the way relationship()/backref() automatically
        populates the other side.
        '''
        from adhocracy.model import Poll
        (proposal, _) = self._make_proposal(voting=True)
        adopt_polls = [poll for poll in proposal.polls if
                       poll.action == Poll.ADOPT]
        self.assertEqual(len(adopt_polls), 2)
        self.assertTrue(adopt_polls[0] is adopt_polls[1])

    def test_delete_deletes_polls(self):
        (proposal, _) = self._make_proposal(voting=True)
        proposal.delete()
        self.assertTrue(len(proposal.polls) > 0)
        for poll in proposal.polls:
            self.assertTrue(poll.is_deleted())

    def test_proposal_description(self):
        '''
        When we create an Proposal, we create a Description object.
        '''
        from adhocracy.model import Description
        (proposal, _) = self._make_proposal()
        self.assertTrue(isinstance(proposal.description, Description))
        self.assertTrue(proposal.creator is proposal.description.creator)
        self.assertTrue(proposal.description in proposal.children)
