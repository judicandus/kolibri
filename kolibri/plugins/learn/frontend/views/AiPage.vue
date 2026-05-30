<template>

  <LearnAppBarPage :appBarTitle="learnString('learnLabel')">
    <div class="ai-container">
      <iframe
        src="https://ai.angelsforedu.org/"
        class="ai-iframe"
        frameborder="0"
        allow="microphone; camera"
        allowfullscreen
      />
    </div>
  </LearnAppBarPage>

</template>


<script>

  import commonLearnStrings from './commonLearnStrings';
  import LearnAppBarPage from './LearnAppBarPage';

  export default {
    name: 'AiPage',
    metaInfo() {
      return {
        title: 'AI',
      };
    },
    components: {
      LearnAppBarPage,
    },
    mixins: [commonLearnStrings],
  };

</script>


<style lang="scss" scoped>

  .ai-container {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
  }

  .ai-iframe {
    width: 100%;
    height: 100%;
    border: none;
  }

</style>
