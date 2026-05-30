<template>

  <router-link
    :to="to"
    class="card-link"
    :class="[themeClasses.link, { 'card-link-with-thumbnail': !!thumbnailUrl }]"
  >
    <img
      v-if="thumbnailUrl"
      :src="thumbnailUrl"
      alt=""
      class="card-thumbnail"
      loading="lazy"
    >
    <slot></slot>
  </router-link>

</template>


<script>

  export default {
    name: 'CardLink',
    props: {
      to: {
        type: Object,
        required: true,
      },
      thumbnailUrl: {
        type: String,
        required: false,
        default: '',
      },
    },
    computed: {
      themeClasses() {
        const { surface, text } = this.$themeTokens;
        return {
          link: this.$computedClass({
            ':focus': this.$coreOutline,
            color: text,
            backgroundColor: surface,
          }),
        };
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kolibri-design-system/lib/styles/definitions';

  .card-link {
    @extend %dropshadow-1dp;

    display: inline-block;
    padding: 16px;
    text-decoration: none;
    border-radius: 8px;
    transition: box-shadow $core-time ease;

    &:hover {
      @extend %dropshadow-6dp;
    }
  }

  .card-link-with-thumbnail {
    position: relative;
    overflow: hidden;
  }

  .card-thumbnail {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: 75% center;
    z-index: 0;
  }

</style>
