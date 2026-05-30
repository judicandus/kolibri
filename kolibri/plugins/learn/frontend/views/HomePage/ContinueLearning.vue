<template>

  <section v-if="lesson">
    <h2>
      <KLabeledIcon
        icon="forward"
        :label="$tr('continueLearningFromClassesHeader')"
      />
    </h2>

    <router-link
      :to="lessonLink"
      class="hero-card"
      :class="[$computedClass({ ':focus': $coreOutline })]"
    >
      <img
        v-if="thumbnailUrl"
        class="hero-image"
        :src="thumbnailUrl"
        alt=""
        loading="lazy"
      >
      <div class="hero-overlay">
        <span class="hero-badge">
          {{ $tr('continueWatching') }}
        </span>
        <p
          v-if="className"
          class="hero-class"
        >
          {{ className }}
        </p>
        <h3 class="hero-title">
          {{ lesson.title }}
        </h3>
        <div
          v-if="firstResource"
          class="hero-meta"
        >
          <LearningActivityLabel
            :contentNode="firstResource"
            :hideDuration="false"
          />
        </div>
        <div class="hero-progress-wrapper">
          <div
            class="hero-progress-track"
            role="progressbar"
            :aria-valuemin="0"
            :aria-valuemax="100"
            :aria-valuenow="lessonProgressPercent"
          >
            <div
              class="hero-progress-fill"
              :style="{ width: lessonProgressPercent + '%' }"
            />
          </div>
        </div>
      </div>
    </router-link>
  </section>

</template>


<script>

  import { computed } from 'vue';
  import useLearnerResources from '../../composables/useLearnerResources';
  import LearningActivityLabel from '../LearningActivityLabel';

  /**
   * Shows a single horizontal hero card for the most recent active lesson.
   * The card displays the lesson's first resource thumbnail as a full-bleed
   * background image with lesson info overlaid on the left side.
   */
  export default {
    name: 'ContinueLearning',
    components: {
      LearningActivityLabel,
    },
    setup(props) {
      const { getClass, getClassLessonLink } = useLearnerResources();

      const className = computed(() => {
        if (!props.lesson) return '';
        const cls = getClass(props.lesson.collection);
        return cls ? cls.name : '';
      });

      const lessonLink = computed(() => {
        return getClassLessonLink(props.lesson);
      });

      const firstResource = computed(() => {
        if (
          !props.lesson ||
          !props.lesson.resources ||
          !props.lesson.resources.length
        ) {
          return null;
        }
        return props.lesson.resources[0].contentnode || null;
      });

      const thumbnailUrl = computed(() => {
        if (!firstResource.value) return '';
        return firstResource.value.thumbnail || '';
      });

      const lessonProgressPercent = computed(() => {
        if (!props.lesson || !props.lesson.progress) return 0;
        const { resource_progress, total_resources } = props.lesson.progress;
        if (!total_resources) return 0;
        return Math.round((resource_progress / total_resources) * 100);
      });

      return {
        className,
        lessonLink,
        firstResource,
        thumbnailUrl,
        lessonProgressPercent,
      };
    },
    props: {
      lesson: {
        type: Object,
        required: true,
      },
    },
    $trs: {
      continueLearningFromClassesHeader: {
        message: 'Continue learning from your classes',
        context:
          'Section header for the hero card linking to the most recent active lesson.',
      },
      continueWatching: {
        message: 'Continue Watching',
        context:
          'Badge label on the hero card indicating the learner can continue this lesson.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  .hero-card {
    position: relative;
    display: block;
    width: 100%;
    min-height: 200px;
    overflow: hidden;
    text-decoration: none;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    transition: box-shadow 0.3s ease;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
  }

  .hero-image {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: 75% center;
  }

  .hero-overlay {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    min-height: 200px;
    padding: 24px;
    background: linear-gradient(
      to right,
      rgba(0, 0, 0, 0.65) 0%,
      rgba(0, 0, 0, 0.3) 50%,
      transparent 70%
    );
  }

  .hero-badge {
    display: inline-block;
    align-self: flex-start;
    padding: 4px 12px;
    margin-bottom: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }

  .hero-class {
    margin: 0 0 4px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.85);
  }

  .hero-title {
    margin: 0 0 8px;
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
  }

  .hero-meta {
    margin-bottom: 12px;
    color: rgba(255, 255, 255, 0.85);

    /deep/ .label,
    /deep/ .duration {
      color: rgba(255, 255, 255, 0.85);
    }

    /deep/ svg {
      fill: rgba(255, 255, 255, 0.85);
    }
  }

  .hero-progress-wrapper {
    max-width: 37.5%;
  }

  .hero-progress-track {
    width: 100%;
    height: 4px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }

  .hero-progress-fill {
    height: 100%;
    background: #ffffff;
    border-radius: 2px;
    transition: width 0.3s ease;
  }

</style>
