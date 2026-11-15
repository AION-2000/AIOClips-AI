import unittest
from datetime import datetime, timezone
from app.approval import Short, Status, ApprovalError, submit_for_review, approve, reject, revise, require_publishable, mark_published

class ApprovalTests(unittest.TestCase):
    def ready(self):
        return Short(id="clip-1", rights_verified=True, facts_verified=True,
                     original_content_verified=True, render_ready=True)
    def test_unapproved_cannot_publish(self):
        with self.assertRaises(ApprovalError): require_publishable(self.ready())
    def test_review_is_not_approval(self):
        with self.assertRaises(ApprovalError): require_publishable(submit_for_review(self.ready()))
    def test_missing_rights_block_approval(self):
        with self.assertRaises(ApprovalError):
            approve(submit_for_review(Short(id="x", facts_verified=True, original_content_verified=True, render_ready=True)), reviewer="owner")
    def test_approved_revision_can_publish(self):
        approved=approve(submit_for_review(self.ready()), reviewer="owner", now=datetime.now(timezone.utc))
        self.assertEqual(mark_published(approved).status, Status.PUBLISHED)
    def test_revision_revokes_approval(self):
        approved=approve(submit_for_review(self.ready()), reviewer="owner")
        with self.assertRaises(ApprovalError): require_publishable(revise(approved))
    def test_rejected_cannot_publish(self):
        with self.assertRaises(ApprovalError): require_publishable(reject(submit_for_review(self.ready())))
    def test_blank_reviewer_rejected(self):
        with self.assertRaises(ApprovalError): approve(submit_for_review(self.ready()), reviewer=" ")
    def test_cannot_approve_draft(self):
        with self.assertRaises(ApprovalError): approve(self.ready(), reviewer="owner")

if __name__ == "__main__":
    unittest.main()
