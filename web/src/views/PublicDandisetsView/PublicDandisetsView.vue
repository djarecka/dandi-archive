<template>
  <DandisetsPage title="Public Dandisets" />
</template>

<script lang="ts">
import DandisetsPage from '@/components/DandisetsPage.vue';
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  name: 'PublicDandisetsView',
  components: { DandisetsPage },
});
</script>
