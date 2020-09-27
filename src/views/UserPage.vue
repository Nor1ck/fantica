<template>
  <div>
    <img class="bgs-c" :src="coverURL" width="100%" alt="cover"/>
    <div v-if="profile.about">About me: {{ profile.about }}</div>
    <div v-if="profile.location">Location: {{ profile.location }}</div>
    <div v-if="profile.website">Website:<a :href="profile.website" target="_blank"> {{ profile.website }}</a></div>
    <Post v-for="post in posts" :post="post" :key="post._id" class="mb-5"/>
  </div>
</template>

<script>
import Post from "@/components/Post.vue";

export default {
  name: "Feed",
  components: {
    Post
  },
  data() {
    return {
      posts: [],
      coverURL: null,
      profile: {},
    };
  },
  watch: {
    $route() {
      this.updatePage();
    },
  },
  computed: {
    metamaskAddress() {
      return this.$store.state.metamaskAddress;
    },
  },
  methods: {
    async getPosts() {
      let resp = await this.$http.get(this.$HOST + '/api/posts/' + this.$route.params.address, { withCredentials: true });
      if (resp.status == 200) {
        this.posts = resp.data.posts
      }
    },
    async getProfile() {
      let resp = await this.$http.get(this.$HOST + '/api/profile/' + this.$route.params.address, { withCredentials: true });
      if (resp.status == 200) {
        this.profile = resp.data.profile
      }
    },
    updatePage() {
      this.getPosts()
      this.getProfile()
      this.coverURL = this.$HOST + '/static/cover/' + this.$route.params.address + '/cover.jpg'
    },
  },
  mounted() {
    this.updatePage();
  },
};
</script>

<style lang="scss">
.bgs-c {
  background-size: cover;
  max-height: 150px;
}
</style>