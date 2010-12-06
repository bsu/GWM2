# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.db import models
from django.utils.encoding import force_unicode, smart_unicode

from ganeti.models import Profile
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey


class LogAction(models.Model):
    """
    Type of action of log entry (for example: addition, deletion)

    @param name           string  noun (for example: addition)
    @param action_message string  participle ("-ed" if regular) form of verb
                                  (for example: added)
    """
    name = models.CharField(max_length=128, primary_key=True) #addition, deletion
    action_message = models.CharField(max_length=128)         # added, deleted


class LogItemManager(models.Manager):

    # Cache to avoid re-looking up LogAction objects all over the place
    _cache = {}

    def _add_to_cache(self, using, action):
        """
        Insert LogAction into cache
        @param using  Database   used database
        @param action LogAction  action name
        """
        key = action.name
        self.__class__._cache.setdefault( using, {} )[key] = action

    def _get_action_object(self, name):
        """
        Bridge used to cache actions

        @param name string
        """
        try:
            action = self.__class__._cache[self.db][name]
        except KeyError:
            # get if exists
            # or create otherwise
            action, created = LogAction.objects.get_or_create(
                name = name,
                defaults = { "action_message": "%sed" % smart_unicode(name) },
            )
            # load it into cache
            self._add_to_cache(self.db, action)
        return action

    # TODO: perhaps this needs improving
    # take a look at django.contrib.contenttypes.management.update_contenttypes
    def clear_cache(self):
        """
        Clears out all LogAction cached objects
        """
        self.__class__._cache.clear()

    def log_action(self, user, affected_object, action, log_message=None):
        """
        Creates new log entry

        @param user             Profile
        @param affected_object  any model
        @param action           string or LogAction
        """
        if isinstance(action, str):
            action = self._get_action_object(action)
        else:
            # just adds to cache it action obj. not yet added
            try:
                act = self.__class__._cache[self.db][action.name]
            except KeyError:
                self._add_to_cache(self.db, action)

        m = self.model(
            id = None,
            action = action,
            timestamp = None,
            user = user, # or user.pk or request.user.pk
            object_type = ContentType.objects.get_for_model(affected_object),
            object_id = affected_object.pk,
            object_repr = force_unicode(affected_object),
            log_message = log_message,
        )
        m.save()
        return m.id # occasionally someone needs this


class LogItem(models.Model):
    """
    Single entry in log
    """
    action = models.ForeignKey(LogAction)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Profile)

    object_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=128, blank=True, null=True)
    affected_object = GenericForeignKey("object_type", "object_id")

    log_message = models.TextField(blank=True, null=True)

    objects = LogItemManager()

    class Meta:
        ordering = ("timestamp", )

    def __repr__(self):
        """
        Returns single line log entry containing informations like:
        - date and extensive time
        - user who performed an action
        - action itself
        - object affected by the action
        """
        # this format:
        #[2010-11-30 14:12:31] user piotr changed user "piotr": root=True, abc=True
        #[2010-11-30 14:12:31] user piotr deleted virtual machine "testfarm1"
        msg = ""
        if self.log_message:
            msg = ": %s" % self.log_message

        format = "[%(timestamp)s] user %(user)s %(action_message)s" \
               + " %(object_type)s \"%(object_repr)s\"%(msg)s"

        fields = dict(
            timestamp = self.timestamp,
            user = self.user,
            action_message = self.action.action_message,
            object_type = self.object_type.name,
            object_repr = self.object_repr,
            msg = msg,
        )
        return format % fields