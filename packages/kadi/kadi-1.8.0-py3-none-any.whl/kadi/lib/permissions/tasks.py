# Copyright 2021 Karlsruhe Institute of Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import kadi.lib.constants as const
from kadi.ext.celery import celery
from kadi.ext.db import db
from kadi.lib.permissions.models import RoleRule
from kadi.lib.tasks.core import launch_task
from kadi.modules.accounts.models import User

from .core import apply_role_rule


@celery.task(name=const.TASK_APPLY_ROLE_RULES)
def _apply_role_rules_task(role_rule_id, user_id, **kwargs):
    user = None

    if user_id is not None:
        user = User.query.get(user_id)

        # Don't apply any rules if no user was found for the given ID
        if user is None:
            return False

    if role_rule_id is not None:
        role_rule = RoleRule.query.get(role_rule_id)

        if role_rule is None:
            return False

        apply_role_rule(role_rule, user=user)
        db.session.commit()
    else:
        # Always iterate through the rules in a consistent order (their creation date),
        # in case there are multiple rules for the same resource applying different
        # roles to the same user.
        for role_rule in RoleRule.query.order_by(RoleRule.created_at):
            apply_role_rule(role_rule, user=user)
            db.session.commit()

    return True


def start_apply_role_rules_task(role_rule=None, user=None):
    """Apply a specific or all existing role rules in a background task.

    :param role_rule: (optional) A specific role rule to apply.
    :param user: (optional) A specific user to apply the role rule(s) to. If not given,
        all existing users are considered.
    :return: ``True`` if the task was started successfully, ``False`` otherwise.
    """
    role_rule_id = None

    if role_rule is not None:
        role_rule_id = role_rule.id

    user_id = None

    if user is not None:
        user_id = user.id

    return launch_task(const.TASK_APPLY_ROLE_RULES, args=[role_rule_id, user_id])
