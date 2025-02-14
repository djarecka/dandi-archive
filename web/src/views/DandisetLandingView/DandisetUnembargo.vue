<template>
  <v-card
    v-if="currentDandiset"
    outlined
    class="mt-4 px-3"
  >
    <v-dialog
      v-if="showWarningDialog"
      v-model="showWarningDialog"
      persistent
      max-width="60vh"
    >
      <v-card class="pb-3">
        <v-card-title class="text-h5 font-weight-light">
          Unembargo Dandiset
        </v-card-title>
        <v-divider class="my-3" />
        <v-card-text>
          <span>
            This action will unembargo this dandiset. Note that this is a
            <span class="font-weight-bold">
              permanent
            </span>
            action and is not undoable. Once a dandiset has been unembargoed,
            it cannot be re-embargoed.
            <br><br>
            Note: this may take a while if your dandiset is large.
          </span>
        </v-card-text>
        <v-card-text>
          Please enter this dandiset's identifier (
          <span class="font-weight-bold">
            {{ currentDandiset.dandiset.identifier }}
          </span>
          ) to proceed:
          <v-text-field
            v-model="confirmationPhrase"
            style="width: 30%;"
            dense
            outlined
          />
        </v-card-text>

        <v-card-actions>
          <v-btn
            color="error"
            depressed
            :disabled="confirmationPhrase !== currentDandiset.dandiset.identifier"
            @click="unembargo()"
          >
            Yes
          </v-btn>
          <v-btn
            depressed
            @click="showWarningDialog = false"
          >
            No, take me back
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-row
      class="mb-4"
      no-gutters
    >
      <v-tooltip
        left
        :disabled="!unembargoing"
      >
        <template #activator="{ on }">
          <div
            class="px-1 pt-3"
            style="width: 100%"
            v-on="on"
          >
            <v-btn
              block
              color="info"
              depressed
              :disabled="unembargoing"
              @click="unembargo()"
            >
              {{ unembargoing ? 'Unembargoing' : 'Unembargo' }}
              <v-spacer />
              <v-icon>mdi-lock-open</v-icon>
            </v-btn>
          </div>
        </template>
        <span v-if="unembargoing">This dandiset is being unembargoed, please wait.</span>
      </v-tooltip>
    </v-row>
    <v-row>
      <v-subheader class="mb-2 black--text text-h5">
        This Version
      </v-subheader>
    </v-row>
    <v-row
      class="pa-2 mb-5 text-body-2 align-center"
      style="border-top: thin solid rgba(0, 0, 0, 0.12);
             border-bottom: thin solid rgba(0, 0, 0, 0.12);
             text-align: center;"
    >
      <v-col
        :cols="$vuetify.breakpoint.md ? 12 : 4"
        style=""
      >
        {{ formatDate(currentDandiset.modified) }}
      </v-col>
      <v-col>
        <h3>{{ currentDandiset.version.toUpperCase() }}</h3>
      </v-col>
    </v-row>
  </v-card>
</template>

<script lang="ts">
import { computed, defineComponent, ref } from '@vue/composition-api';
import moment from 'moment';
import { dandiRest } from '@/rest';
import store from '@/store';

function formatDate(date: string): string {
  return moment(date).format('ll');
}

export default defineComponent({
  name: 'DandisetUnembargo',
  setup() {
    const currentDandiset = computed(() => store.state.dandiset.dandiset);
    const unembargoing = computed(() => currentDandiset.value?.dandiset.embargo_status === 'UNEMBARGOING');
    const showWarningDialog = ref(false);
    const confirmationPhrase = ref('');

    async function unembargo() {
      if (currentDandiset.value) {
        // Display the warning dialog before releasing
        if (!showWarningDialog.value) {
          showWarningDialog.value = true;
          return;
        }

        await dandiRest.unembargo(currentDandiset.value.dandiset.identifier);

        // re-fetch the dandiset to refresh the embargo_status
        store.dispatch.dandiset.fetchDandiset({
          identifier: currentDandiset.value.dandiset.identifier,
          version: currentDandiset.value.version,
        });

        showWarningDialog.value = false;
      }
    }

    return {
      currentDandiset,
      showWarningDialog,
      unembargoing,
      confirmationPhrase,
      unembargo,
      formatDate,
    };
  },
});
</script>
