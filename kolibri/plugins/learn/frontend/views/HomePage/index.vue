<template>

  <div>
    <transition name="delay-entry">
      <PostSetupModalGroup
        v-if="welcomeModalVisible && isLearner"
        isOnMyOwnUser
        @cancel="hideWelcomeModal"
      />
    </transition>
    <LearnAppBarPage :appBarTitle="learnString('learnLabel')">
      <div
        v-if="!loading"
        role="main"
      >
        <ResourceSyncingUiAlert
          v-if="missingResources"
          @syncComplete="hydrateHomePage"
        />
        <YourClasses
          v-if="displayClasses"
          class="section"
          :classes="classes"
          data-test="classes"
          short
        />
        <ContinueLearning
          v-if="mostRecentLesson"
          class="section"
          :lesson="mostRecentLesson"
          data-test="continueLearningFromClasses"
        />
        <RecentlyAccessed
          v-if="recentResources.length > 0"
          class="section"
          :resources="recentResources"
          data-test="recentlyAccessed"
        />
        <AssignedQuizzesCards
          v-if="hasActiveClassesQuizzes"
          class="section"
          :quizzes="activeClassesQuizzes"
          displayClassName
          recent
          data-test="recentQuizzes"
        />
        <ExploreChannels
          v-if="displayExploreChannels"
          :channels="channels"
          class="section"
          data-test="exploreChannels"
          :short="
            Boolean(
              displayClasses ||
                mostRecentLesson ||
                recentResources.length > 0 ||
                hasActiveClassesQuizzes,
            )
          "
        />
      </div>
    </LearnAppBarPage>
  </div>

</template>


<script>

  import { computed, getCurrentInstance } from 'vue';
  import { get, set } from '@vueuse/core';
  import uniqBy from 'lodash/uniqBy';
  import flatMapDepth from 'lodash/flatMapDepth';
  import client from 'kolibri/client';
  import urls from 'kolibri/urls';
  import useUser from 'kolibri/composables/useUser';
  import useChannels from 'kolibri-common/composables/useChannels';
  import { mapState } from 'vuex';
  import ResourceSyncingUiAlert from '../ResourceSyncingUiAlert';
  import useDeviceSettings from '../../composables/useDeviceSettings';
  import useLearnerResources, {
    setClasses,
    setResumableContentNodes,
  } from '../../composables/useLearnerResources';
  import { setContentNodeProgress } from '../../composables/useContentNodeProgress';
  import { inClasses } from '../../composables/useCoreLearn';
  import { PageNames } from '../../constants';
  import AssignedQuizzesCards from '../classes/AssignedQuizzesCards';
  import YourClasses from '../YourClasses';
  import LearnAppBarPage from '../LearnAppBarPage';
  import PostSetupModalGroup from '../../../../device/frontend/views/PostSetupModalGroup.vue';
  import commonLearnStrings from './../commonLearnStrings';
  import ContinueLearning from './ContinueLearning';
  import RecentlyAccessed from './RecentlyAccessed';
  import ExploreChannels from './ExploreChannels';

  /**
   * Home page contains useful suggestions for a learner, e.g. their
   * resources and quizzes in progress, classes, resources to explore, etc.
   * What sections are displayed depends on whether a learner
   * is signed in and also if they're a member of classes.
   */
  const welcomeDismissalKey = 'DEVICE_WELCOME_MODAL_DISMISSED';
  export default {
    name: 'HomePage',
    components: {
      AssignedQuizzesCards,
      YourClasses,
      ContinueLearning,
      RecentlyAccessed,
      ExploreChannels,
      LearnAppBarPage,
      ResourceSyncingUiAlert,
      PostSetupModalGroup,
    },
    mixins: [commonLearnStrings],
    setup() {
      const currentInstance = getCurrentInstance().proxy;
      const store = currentInstance.$store;
      const router = currentInstance.$router;

      const { isUserLoggedIn, user_id, isLearner } = useUser();
      const { canAccessUnassignedContent } = useDeviceSettings();
      const { localChannelsCache, fetchChannels } = useChannels();
      const {
        classes,
        activeClassesLessons,
        activeClassesQuizzes,
        resumableClassesQuizzes,
        resumableClassesResources,
        resumableContentNodes,
        learnerFinishedAllClasses,
      } = useLearnerResources();

      // Hero card: first active lesson from any class
      const mostRecentLesson = computed(() => {
        const lessons = get(activeClassesLessons);
        return lessons.length > 0 ? lessons[0] : null;
      });

      // Recently accessed: last 4 resources from active class lessons
      const recentResources = computed(() => {
        const allResources = flatMapDepth(
          get(classes),
          c =>
            c.lessons.map(l =>
              l.resources.map(r => ({
                contentNodeId: r.contentnode_id,
                progress: r.progress,
                lessonId: l.id,
                classId: c.id,
                contentNode: r.contentnode,
              })),
            ),
          2,
        );
        return uniqBy(
          allResources.filter(
            r => r.contentNode && r.contentNode.title !== '__class_thumb__',
          ),
          'contentNodeId',
        ).slice(0, 4);
      });
      const hasActiveClassesQuizzes = computed(
        () =>
          get(isUserLoggedIn) && get(activeClassesQuizzes) && get(activeClassesQuizzes).length > 0,
      );
      const hasChannels = computed(() => {
        return get(localChannelsCache).length > 0;
      });
      const displayExploreChannels = computed(() => {
        return (
          get(hasChannels) &&
          (!get(isUserLoggedIn) ||
            (get(learnerFinishedAllClasses) && get(canAccessUnassignedContent)))
        );
      });

      const displayClasses = computed(() => {
        return get(isUserLoggedIn) && (get(classes).length || !get(canAccessUnassignedContent));
      });

      const missingResources = computed(() => {
        return (
          get(activeClassesLessons).some(l => l.missing_resource) ||
          get(activeClassesQuizzes).some(q => q.missing_resource)
        );
      });

      function hydrateHomePage() {
        return client({ url: urls['kolibri:kolibri.plugins.learn:homehydrate']() }).then(
          response => {
            setClasses(response.data.classrooms);
            // Update our hydrated class membership boolean in case it has changed
            // since the learn page was opened.
            set(inClasses, Boolean(response.data.classrooms.length));
            setResumableContentNodes(
              response.data.resumable_resources.results || [],
              response.data.resumable_resources.more || null,
            );
            for (const progress of response.data.resumable_resources_progress) {
              setContentNodeProgress(progress);
            }
          },
        );
      }

      fetchChannels().then(channels => {
        if (!channels.length) {
          router.replace({ name: PageNames.LIBRARY });
          return;
        }

        // force fetch classes and resumable content nodes to make sure that the home
        // page is up-to-date when navigating to other 'Learn' pages and then back
        // to the home page
        return hydrateHomePage()
          .then(() => {
            store.commit('SET_PAGE_NAME', PageNames.HOME);
            store.dispatch('notLoading');
          })
          .catch(error => {
            return store.dispatch('handleApiError', { error, reloadOnReconnect: true });
          });
      });

      return {
        channels: localChannelsCache,
        classes,
        activeClassesLessons,
        activeClassesQuizzes,
        mostRecentLesson,
        recentResources,
        hasActiveClassesQuizzes,
        displayExploreChannels,
        displayClasses,
        missingResources,
        hydrateHomePage,
        userId: user_id,
        isLearner,
      };
    },
    props: {
      loading: {
        type: Boolean,
        default: null,
      },
    },
    computed: {
      ...mapState({
        welcomeModalVisibleState: 'welcomeModalVisible',
      }),
      welcomeModalVisible() {
        return (
          this.welcomeModalVisibleState &&
          window.localStorage.getItem(`${welcomeDismissalKey}-${this.userId}`) !== 'true'
        );
      },
    },
    created() {
      const welcomeDismissalKey = 'DEVICE_WELCOME_MODAL_DISMISSED';
      if (window.sessionStorage.getItem(`${welcomeDismissalKey}-${this.userId}`) !== 'true') {
        this.$store.commit('SET_WELCOME_MODAL_VISIBLE', true);
      }
    },
    methods: {
      hideWelcomeModal() {
        window.localStorage.setItem(`${welcomeDismissalKey}-${this.userId}`, true);
        this.$store.commit('SET_WELCOME_MODAL_VISIBLE', false);
      },
    },
  };

</script>


<style lang="scss" scoped>

  .section:not(:first-child) {
    margin-top: 32px;
  }

  .section:first-child {
    margin-top: 16px;
  }

</style>
