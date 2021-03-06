# Copyright (C) 2010 Oregon State University et al.
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

from django.conf import settings
from ganeti_web.models import Cluster


def site(request):
    """
    adds site properties to the context
    """    
    return {'SITE_DOMAIN':settings.SITE_DOMAIN, 'SITE_NAME':settings.SITE_NAME}


ANONYMOUS_PERMISSIONS = dict(cluster_admin=False,
                             create_vm=False,
                             view_cluster=False)

CLUSTER_ADMIN_PERMISSIONS = dict(cluster_admin=True,
                             create_vm=True,
                             view_cluster=True)

def common_permissions(request):
    """
    adds common cluster perms to the context:

        * cluster_admin
        * view_cluster
        * create vm
    """
    user = request.user
    if user.is_authenticated():
        if user.is_superuser:
            return CLUSTER_ADMIN_PERMISSIONS

        perms = user.get_perms_any(Cluster)

        if 'admin' in perms:
            return CLUSTER_ADMIN_PERMISSIONS

        else:
            create_vm = 'create_vm' in perms
            view_cluster = any((p in perms for p in ['migrate','export','replace_disks','tags']))
        
        return {
            'cluster_admin':False,
            'create_vm':create_vm,
            'view_cluster':view_cluster
        }

    return ANONYMOUS_PERMISSIONS