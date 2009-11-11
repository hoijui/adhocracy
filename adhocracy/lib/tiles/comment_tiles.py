from pylons import tmpl_context as c
from webhelpers.text import truncate

import adhocracy.model as model
from .. import text
from .. import karma
from .. import authorization as auth
from .. import democracy
from .. import sorting

from util import render_tile, BaseTile

class CommentTile(BaseTile):
    
    def __init__(self, comment):
        self.comment = comment
        
    def _num_motions(self):
        return len(self.issue.motions)
    
    num_motions = property(_num_motions)
    
    def _text(self):       
        if self.comment and self.comment.latest:
            return text.render(self.comment.latest.text)
        return ""
    
    text = property(_text)
    
    def _tagline(self):       
        if self.comment.latest:
            tagline = text.plain(self.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _on_motion(self):
        return isinstance(self.comment.topic, model.Motion)
    
    on_motion = property(_on_motion)
    
    def _on_issue(self):
        return isinstance(self.comment.topic, model.Issue)
    
    on_issue = property(_on_issue)
    
    def _can_edit(self):
        return auth.on_comment(self.comment, 'comment.edit') \
                and not self.is_deleted and not self.is_immutable
    
    can_edit = property(_can_edit)        
    lack_edit_karma = property(BaseTile.prop_lack_karma('comment.edit'))
    
    def _can_delete(self):
        if auth.on_comment(self.comment, 'comment.delete') \
            and not self.is_deleted and not self.is_immutable:
            if self.comment.reply or self.comment.canonical:
                return True
        return False
    
    can_delete = property(_can_delete)
    lack_delete_karma = property(BaseTile.prop_lack_karma('comment.delete'))
    
    def _can_reply(self):        
        return auth.on_delegateable(self.comment.topic, 'comment.create') \
                and not self.is_deleted
    
    can_reply = property(_can_reply)
    lack_reply_karma = property(BaseTile.prop_lack_karma('comment.create'))
    
    def _can_give_karma(self):
        return auth.on_comment(self.comment, 'karma.give') \
                and not self.is_own \
                and not self.is_deleted and not self.is_immutable
    
    can_give_karma = property(_can_give_karma)
    lack_give_karma_karma = property(BaseTile.prop_lack_karma('karma.give'))
    
    def _is_own(self):
        return self.comment.creator == c.user
    
    is_own = property(_is_own)
    
    def _is_edited(self):
        if self.is_deleted:
            return False
        return len(self.comment.revisions) > 1
    
    is_edited = property(_is_edited)
    
    def _is_deleted(self):
        return self.comment.delete_time
    
    is_deleted = property(_is_deleted)
    
    def _is_immutable(self):
        return not democracy.is_comment_mutable(self.comment)
    
    is_immutable = property(_is_immutable)

    def _show(self):
        if self.is_deleted:
            children = map(lambda c: CommentTile(c)._show(), self.comment.replies) 
            if not True in children:
                return False
        return True
    
    show = property(_show)
    
    def _num_children(self):
        num = len(filter(lambda c: not c.delete_time, self.comment.replies))
        num += sum(map(lambda c: CommentTile(c)._num_children(), self.comment.replies))
        return num
    
    num_children = property(_num_children)
    
    def _karma_score(self):
        return karma.comment_score(self.comment)
    
    karma_score = property(_karma_score)
    
    def _karma_position(self):
        if not c.user:
            return None
        pos = karma.position(self.comment, c.user)
        if (pos and pos.value == 1) or self.comment.creator == c.user:
            return "upvoted"
        elif pos and pos.value == -1:
            return "downvoted"
        return pos
    
    karma_position = property(_karma_position)
    
    def _replies(self):
        return sorting.comment_karma(self.comment.replies)
    
    replies = property(_replies)


def row(comment):
    return render_tile('/comment/tiles.html', 'row', CommentTile(comment), comment=comment)    

def full(comment, recurse=True, collapse=True, link_discussion=False):
    return render_tile('/comment/tiles.html', 'full', CommentTile(comment), 
                       recurse=recurse, comment=comment, collapse=collapse, link_discussion=link_discussion)

