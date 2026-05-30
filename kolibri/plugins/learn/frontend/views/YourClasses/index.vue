<template>

  <section>
    <KFixedGrid :numCols="3">
      <KFixedGridItem :span="2">
        <h2 :style="{ marginTop: 0 }">
          <KLabeledIcon
            icon="classes"
            :label="$tr('yourClassesHeader')"
          />
        </h2>
      </KFixedGridItem>
      <KFixedGridItem
        :span="1"
        alignment="right"
      >
        <KRouterLink
          v-if="displayAllClassesLink"
          :text="coreString('viewAll')"
          :to="allClassesLink"
          data-test="viewAllLink"
        />
      </KFixedGridItem>
    </KFixedGrid>

    <CardGrid
      v-if="classes && classes.length > 0"
      :gridType="2"
    >
      <CardLink
        v-for="c in visibleClasses"
        :key="c.id"
        class="class-card"
        data-test="classLink"
        :to="classAssignmentsLink(c.id)"
        :style="classCardStyle(c)"
      >
        <h3
          dir="auto"
          class="class-card-title"
        >
          {{ c.name }}
        </h3>
      </CardLink>
    </CardGrid>

    <KCircularLoader v-else-if="loading" />

    <p v-else-if="!loading">
      {{ $tr('noClasses') }}
    </p>
  </section>

</template>


<script>

  import commonCoreStrings from 'kolibri/uiText/commonCoreStrings';
  import { ClassesPageNames } from '../../constants';
  import { classAssignmentsLink } from '../classes/classPageLinks';
  import CardGrid from '../cards/CardGrid';
  import CardLink from '../cards/CardLink';

  /**
   * Shows learner's classes.
   */
  export default {
    name: 'YourClasses',
    components: {
      CardGrid,
      CardLink,
    },
    mixins: [commonCoreStrings],
    props: {
      classes: {
        type: Array,
        required: true,
      },
      /**
       * If there is more than four classes, only first four of them
       * and "View all" link will be displayed if `true`
       */
      short: {
        type: Boolean,
        required: false,
        default: false,
      },
      loading: {
        type: Boolean,
        default: null,
      },
    },
    data() {
      return {
        classAssignmentsLink,
      };
    },
    computed: {
      visibleClasses() {
        if (!this.classes) {
          return [];
        }
        if (this.short) {
          return this.classes.slice(0, 4);
        }
        return this.classes;
      },
      allClassesLink() {
        return { name: ClassesPageNames.ALL_CLASSES };
      },
      displayAllClassesLink() {
        return this.classes && this.classes.length > this.visibleClasses.length;
      },
    },
    methods: {
      getClassThumbnail(classObj) {
        if (!classObj || !classObj.lessons) return null;
        for (const lesson of classObj.lessons) {
          if (!lesson.resources) continue;
          for (const resource of lesson.resources) {
            if (
              resource.contentnode &&
              resource.contentnode.title === '__class_thumb__'
            ) {
              return resource.contentnode.thumbnail || null;
            }
          }
        }
        return null;
      },
      classCardStyle(classObj) {
        const thumb = this.getClassThumbnail(classObj);
        if (!thumb) return {};
        return {
          backgroundImage: `url(${thumb})`,
          backgroundSize: 'cover',
          backgroundPosition: '75% center',
          minHeight: '180px',
          position: 'relative',
          padding: 0,
          overflow: 'hidden',
        };
      },
    },
    $trs: {
      yourClassesHeader: {
        message: 'Your classes',
        context: 'Refers to the classes the learner is enrolled in.',
      },
      noClasses: {
        message: 'You are not enrolled in any classes',
        context:
          'Message that a learner sees in the Learn > CLASSES section and in the Learn > HOME section if they are not enrolled in any classes.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  .class-card-title {
    margin: 0;
    font-weight: normal;
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 24px 16px 12px;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
    color: #fff;
    font-size: 1rem;
  }

</style>
