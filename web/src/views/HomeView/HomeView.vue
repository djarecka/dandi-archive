<template>
  <v-container
    fluid
    class="pa-0"
  >
    <v-row>
      <v-img
        src="@/assets/logo.svg"
        class="grey lighten-5"
        position="left"
        max-height="500px"
        contain
      >
        <v-container
          fluid
          class="d-flex flex-column py-0"
          :class="[$vuetify.breakpoint.smAndUp ? 'brain-gradient' : 'hide-brain']"
        >
          <v-row
            class="flex-grow-1"
            justify="center"
            align="center"
          >
            <v-col class="splash-text my-12">
              <div class="text-h2 font-weight-thin text-center light-blue--text text--darken-1">
                The DANDI Archive
              </div>
              <div class="text-h6 font-weight-light text-center">
                The BRAIN Initiative archive for publishing and sharing
                neurophysiology data including electrophysiology,
                optophysiology, and behavioral time-series, and images from
                immunostaining experiments.
              </div>
            </v-col>
          </v-row>
        </v-container>
      </v-img>
    </v-row>
    <v-row no-gutters>
      <v-col class="grey darken-2 pa-12">
        <DandisetSearchField :dense="false" />
      </v-col>
    </v-row>
    <v-row class="flex-grow-0">
      <StatsBar />
    </v-row>
  </v-container>
</template>

<script lang="ts">
import StatsBar from '@/views/HomeView/StatsBar.vue';
import DandisetSearchField from '@/components/DandisetSearchField.vue';
import { computed, defineComponent, watchEffect } from '@vue/composition-api';

export default defineComponent({
  name: 'HomeView',
  components: { StatsBar, DandisetSearchField },
  setup(props, ctx) {
    /**
    * Redirect old hash URLS to the correct one. This is only done on
    * the home page, since any URL with a hash will default to here.
    */
    const currentRoute = computed(() => ctx.root.$route);
    watchEffect(() => {
      const router = ctx.root.$router;
      if (currentRoute.value.hash) {
        const trimmed = router.currentRoute.hash.replace('#', '');
        router.replace(trimmed);
      }
    });

    return {
      // Hack to satisfy template type checker
      $vuetify: (ctx.root as any).$vuetify,
    };
  },
});
</script>

<style scoped>
.brain-gradient {
  height: 100%;
  background-image: linear-gradient(
    to right,
    rgba(250, 250, 250, 0.85),
    rgba(250, 250, 250, 1),
    rgba(250, 250, 250, 1),
    rgba(250, 250, 250, 1)
  );
}

.hide-brain {
  height: 100%;
  background-image: linear-gradient(
    to right,
    rgba(250, 250, 250, 1),
    rgba(250, 250, 250, 1)
  );
}

.splash-text {
  max-width: 560px;
}
</style>
