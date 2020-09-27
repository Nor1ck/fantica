<template>
  <div class="feed">
    <Post v-for="post in posts" :post="post" :key="post._id" class="mb-5"/>
  </div>
</template>

<script>
import Post from "@/components/Post.vue";

export default {
  name: "Feed",
  components: {
    Post,
  },
  data() {
    return {
      posts: [],
    };
  },
  methods: {
    async getPosts() {
      let resp = await this.$http.get(this.$HOST + '/api/posts/recent', { withCredentials: true });
      if (resp.status == 200) {
        this.posts = resp.data.posts
      }
    },
  },
  mounted() {
    this.getPosts()
  }
};
</script>