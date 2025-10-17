<!-- Copyright 2022 Karlsruhe Institute of Technology
   -
   - Licensed under the Apache License, Version 2.0 (the "License");
   - you may not use this file except in compliance with the License.
   - You may obtain a copy of the License at
   -
   -     http://www.apache.org/licenses/LICENSE-2.0
   -
   - Unless required by applicable law or agreed to in writing, software
   - distributed under the License is distributed on an "AS IS" BASIS,
   - WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   - See the License for the specific language governing permissions and
   - limitations under the License. -->

<template>
  <div class="form-group">
    <div class="row align-items-end">
      <div class="col-sm-6">
        <label class="form-control-label">{{ field.label }}</label>
      </div>
      <div class="col-sm-6 d-sm-flex justify-content-end mb-2">
        <slot></slot>
      </div>
    </div>
    <div class="card">
      <div class="card-body p-2">
        <div v-for="(role, index) in roles" :key="role.id">
          <div class="form-row" :class="{'mb-3': index < roles.length - 1}">
            <div v-if="groupRolesEnabled" class="col-md-3 mb-1 mb-md-0">
              <div class="input-group input-group-sm">
                <div class="input-group-prepend">
                  <span class="input-group-text">{{ $t('Type') }}</span>
                </div>
                <select v-model="role.subject_type" class="custom-select" @change="role.subject = null">
                  <option v-for="subjectMeta in subjectTypes" :key="subjectMeta[0]" :value="subjectMeta[0]">
                    {{ subjectMeta[1] }}
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-4 mb-1 mb-md-0" :class="{'col-md-7': !groupRolesEnabled}">
              <div class="input-group input-group-sm">
                <div class="input-group-prepend">
                  <span class="input-group-text">{{ getSubjectTitle(role) }}</span>
                </div>
                <dynamic-selection :key="role.subject_type"
                                   container-classes="select2-single-sm"
                                   :endpoint="getSelectionEndpoint(role)"
                                   :initial-values="getInitialSubject(role)"
                                   :placeholder="getSubjectPlaceholder(role)"
                                   @select="selectSubject(role, $event)"
                                   @unselect="role.subject = null">
                </dynamic-selection>
              </div>
            </div>
            <div class="col-md-3 mb-1 mb-md-0">
              <div class="input-group input-group-sm">
                <div class="input-group-prepend">
                  <span class="input-group-text">{{ $t('Role') }}</span>
                </div>
                <select v-model="role.role" class="custom-select">
                  <option v-if="field.allow_none" value=""></option>
                  <option v-for="roleMeta in field.roles" :key="roleMeta[0]" :value="roleMeta[0]">
                    {{ roleMeta[1] }}
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-2">
              <div class="btn-group btn-group-sm w-100">
                <button type="button" class="btn btn-light" :title="$t('Add role')" @click="addRole(null, index)">
                  <i class="fa-solid fa-plus"></i>
                </button>
                <button v-if="roles.length > 1"
                        type="button"
                        class="btn btn-light"
                        :title="$t('Remove role')"
                        @click="removeRole(index)">
                  <i class="fa-solid fa-xmark"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <small class="form-text text-muted">{{ field.description }}</small>
    <input type="hidden" :name="field.name" :value="serializedRoles">
  </div>
</template>

<script>
export default {
  props: {
    field: Object,
    usersEndpoint: String,
    // Optional, since some resources currently do not support group roles. The selection can simply be hidden in this
    // case, as the default subject type can stay as is for all roles.
    groupsEndpoint: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      subjectTypes: [['user', $t('User')], ['group', $t('Group')]],
      roles: [],
    };
  },
  computed: {
    groupRolesEnabled() {
      return this.groupsEndpoint !== null;
    },
    serializedRoles() {
      const roles = [];

      for (const role of this.roles) {
        if (role.subject !== null) {
          roles.push({
            subject_type: role.subject_type,
            subject_id: role.subject[0],
            role: role.role || null,
          });
        }
      }

      return JSON.stringify(roles);
    },
  },
  mounted() {
    for (const role of this.field.data) {
      this.addRole(role);
    }

    if (this.roles.length === 0) {
      this.addRole();
    }
  },
  methods: {
    getSubjectTitle(role) {
      return this.subjectTypes.find((subject) => subject[0] === role.subject_type)[1];
    },
    getSubjectPlaceholder(role) {
      return role.subject_type === 'user' ? $t('Search for users') : $t('Search for groups');
    },
    getSelectionEndpoint(role) {
      return role.subject_type === 'user' ? this.usersEndpoint : this.groupsEndpoint;
    },
    getInitialSubject(role) {
      return role.subject === null ? [] : [role.subject];
    },
    selectSubject(role, subject) {
      role.subject = [subject.id, subject.text];

      // Automatically add a new role input if the last one is not empty.
      if (this.roles[this.roles.length - 1].subject !== null) {
        this.addRole();
      }

      // Dispatch a regular 'change' event from the element as well.
      this.$el.dispatchEvent(new Event('change', {bubbles: true}));
    },
    addRole(role = null, index = null) {
      const newRole = {
        id: kadi.utils.randomAlnum(),
        subject_type: this.subjectTypes[0][0],
        subject: null,
        role: this.field.roles[0][0],
      };

      if (role !== null) {
        // Copy a given role.
        Object.assign(newRole, role);
      } else {
        // Try to copy the subject type and role of the previous role.
        const prevIndex = index === null ? this.roles.length - 1 : index;
        const prevRole = this.roles[prevIndex];

        if (prevRole) {
          newRole.subject_type = prevRole.subject_type;
          newRole.role = prevRole.role;
        }
      }

      kadi.utils.addToArray(this.roles, newRole, index);
    },
    removeRole(index) {
      this.roles.splice(index, 1);
    },
  },
};
</script>
