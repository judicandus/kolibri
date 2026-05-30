<template>

  <section v-if="limitedResources.length > 0">
    <h2>
      <KLabeledIcon
        icon="history"
        :label="$tr('recentlyAccessedHeader')"
      />
    </h2>

    <CardGrid :gridType="2">
      <ResourceCard
        v-for="(resource, idx) in limitedResources"
        :key="idx"
        :contentNode="resource.contentNode"
        :to="genContentLinkBackLinkCurrentPage(resource.contentNode.id, true)"
        :collectionTitle="getResourceClassName(resource)"
        @openCopiesModal="openCopiesModal"
      />
    </CardGrid>

    <CopiesModal
      v-if="displayedCopies.length"
      :copies="displayedCopies"
      @closeModal="closeCopiesModal"
    />
  </section>

</template>


<script>

  import { computed, ref } from 'vue';
  import CardGrid from '../cards/CardGrid';
  import ResourceCard from '../cards/ResourceCard';
  import CopiesModal from '../CopiesModal';
  import useLearnerResources from '../../composables/useLearnerResources';
  import useContentLink from '../../composables/useContentLink';

  export default {
    name: 'RecentlyAccessed',
    components: {
      CardGrid,
      ResourceCard,
      CopiesModal,
    },
    setup(props) {
      const { getClass } = useLearnerResources();
      const { genContentLinkBackLinkCurrentPage } = useContentLink();

      const limitedResources = computed(() => {
        return (props.resources || []).slice(0, 4);
      });

      function getResourceClassName(resource) {
        const resourceClass = getClass(resource.classId);
        return resourceClass ? resourceClass.name : '';
      }

      const displayedCopies = ref([]);

      function openCopiesModal(copies) {
        displayedCopies.value = copies;
      }

      function closeCopiesModal() {
        displayedCopies.value = [];
      }

      return {
        limitedResources,
        getResourceClassName,
        genContentLinkBackLinkCurrentPage,
        displayedCopies,
        openCopiesModal,
        closeCopiesModal,
      };
    },
    props: {
      resources: {
        type: Array,
        required: true,
      },
    },
    $trs: {
      recentlyAccessedHeader: {
        message: 'Recently accessed',
        context:
          'Section header on the learner Home page showing recently accessed content items.',
      },
    },
  };

</script>
