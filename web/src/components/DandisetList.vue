<template>
  <v-list
    three-line
    subheader
  >
    <v-list-item
      v-for="item in dandisets"
      :key="item.dandiset.identifier"
      selectable
      :to="{
        name: 'dandisetLanding',
        params: { identifier: item.dandiset.identifier, origin }
      }"
    >
      <v-list-item-content>
        <v-list-item-title class="wrap-text text-h6 grey--text text--darken-3 pb-1">
          {{ item.name }}
        </v-list-item-title>
        <v-list-item-subtitle>
          <v-chip
            v-if="item.version && item.version !== 'draft'"
            class="mr-1"
            small
            color="light-blue lighten-4"
            text-color="light-blue darken-3"
          >
            <b>{{ item.version }}</b>
          </v-chip>
          <v-chip
            v-else
            x-small
            class="mr-1 px-2"
            color="amber lighten-3"
            text-color="amber darken-4"
          >
            <b>DRAFT</b>
          </v-chip>
          <v-chip
            v-if="item.dandiset.embargo_status !== 'OPEN'"
            x-small
            class="mr-1 px-2"
            :color="`${item.dandiset.embargo_status === 'EMBARGOED' ? 'red' : 'green'} lighten-4`"
            :text-color="
              `${item.dandiset.embargo_status === 'EMBARGOED' ? 'red' : 'green'} darken-3`
            "
          >
            <b>{{ item.dandiset.embargo_status }}</b>
          </v-chip>

          DANDI:<b>{{ item.dandiset.identifier }}</b>
          ·
          Contact <b>{{ item.contact_person }}</b>
          ·
          Updated on <b>{{ formatDate(item.modified) }}</b>
          ·
          <template v-if="dandisets">
            <v-icon
              small
              class="pb-1"
            >
              mdi-file
            </v-icon>
            {{ item.asset_count }}
            ·
            <v-icon
              small
              class="pb-1"
            >
              mdi-database
            </v-icon>
            {{ filesize(item.size, { round: 1, base: 10, standard: 'iec' }) }}
          </template>
        </v-list-item-subtitle>
      </v-list-item-content>
    </v-list-item>
  </v-list>
</template>

<script lang="ts">
import { defineComponent, computed, PropType } from '@vue/composition-api';
import moment from 'moment';
import filesize from 'filesize';

import { Version } from '@/types';

export default defineComponent({
  name: 'DandisetList',
  props: {
    dandisets: {
      type: Array as PropType<Version[]>,
      required: true,
    },
  },
  setup(props, ctx) {
    // Will be replaced by `useRoute` if vue-router is upgraded to vue-router@next
    // https://next.router.vuejs.org/api/#useroute
    const route = ctx.root.$route;

    const origin = computed(() => {
      const { name, params, query } = route;
      return { name, params, query };
    });

    function formatDate(date: string) {
      return moment(date).format('LL');
    }

    return {
      origin,
      formatDate,

      // Returned imports
      filesize,
    };
  },
});
</script>

<style scoped>
.wrap-text {
  -webkit-line-clamp: unset !important;
}
.v-list-item__title {
  white-space: normal;
}

.v-list-item {
  border-bottom: 1px solid #eee;
}

.v-list--three-line .v-list-item .v-list-item__content,
.v-list-item--three-line .v-list-item__content {
  align-self: center;
}
</style>
