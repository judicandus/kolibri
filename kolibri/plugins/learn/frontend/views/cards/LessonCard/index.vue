<template>

  <BaseCard
    v-if="lesson"
    v-bind="{ to, title, collectionTitle, completedLabel, inProgressLabel, thumbnailUrl }"
  />

</template>


<script>

  import { ref, onMounted } from 'vue';
  import commonCoreStrings from 'kolibri/uiText/commonCoreStrings';
  import BaseCard from '../BaseCard';

  export default {
    name: 'LessonCard',
    components: {
      BaseCard,
    },
    mixins: [commonCoreStrings],
    setup(props) {
      const thumbnailUrl = ref('');

      onMounted(() => {
        const resources = props.lesson && props.lesson.resources;
        if (resources && resources.length) {
          for (const resource of resources) {
            if (
              resource.contentnode &&
              resource.contentnode.thumbnail &&
              resource.contentnode.title !== '__class_thumb__'
            ) {
              thumbnailUrl.value = resource.contentnode.thumbnail;
              break;
            }
          }
        }
      });

      return { thumbnailUrl };
    },
    props: {
      lesson: {
        type: Object,
        required: true,
      },
      /**
       * vue-router link object
       */
      to: {
        type: Object,
        required: true,
      },
      collectionTitle: {
        type: String,
        required: false,
        default: '',
      },
    },
    data() {
      return {
        progress: this.lesson ? this.lesson.progress : undefined,
        title: this.lesson ? this.lesson.title : '',
      };
    },
    computed: {
      lessonProgress() {
        if (!this.progress) {
          return NaN;
        }
        const { resource_progress, total_resources } = this.progress;
        if (resource_progress * total_resources === 0) {
          return NaN;
        } else {
          return resource_progress - total_resources;
        }
      },
      inProgressLabel() {
        return this.lessonProgress < 0 ? this.coreString('inProgressLabel') : '';
      },
      completedLabel() {
        return this.lessonProgress >= 0 ? this.coreString('completedLabel') : '';
      },
    },
  };

</script>


<style lang="scss" scoped></style>
