<template>
  <div class="home">
    <div v-for="post in posts" :key="post._id" class="mb-5">
      <h3>{{post.message}}</h3>
      <span v-for="(media, index) in post.media" :key="index"></span>
      <v-btn outlined rounded color="indigo" @click="purchase(post._id)">Buy</v-btn>
    </div>

    <!-- <img src="../assets/empty.jpg" width="200" alt="">
    <v-row>
        <v-col>
            <v-btn outlined rounded color="indigo">Buy</v-btn>
        </v-col>
    </v-row> -->

    <!-- <HelloWorld msg="Welcome to Your Vue.js App" /> -->
  </div>
</template>

<script>

export default {
  name: "Feed",
  components: {

  },
  data() {
    return {
      posts: [],
    };
  },
  computed: {
    metamaskAddress() {
      return this.$store.state.metamaskAddress;
    },
    profile() {
      return this.$store.state.profile;
    },
    fanticaDAppAddress() {
      return this.$store.state.fanticaDAppAddress;
    },
    fanticaDAppABI() {
      return this.$store.state.fanticaDAppABI;
    },
  },
  methods: {
    async getPosts() {
      let resp = await this.$http.get(this.$HOST + '/api/posts', { withCredentials: true });
      if (resp.status == 200) {
        this.posts = resp.data.posts
        // this.$store.commit('setProfile', resp.data.profile);
      }
    },
    async purchase(postId) {
      let creator = postId.split(':')[0];
      let contentId = postId.split(':')[1];
      console.log(creator);
      console.log(contentId);
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.purchase(creator, contentId).send();
    },
  },
  mounted() {
    this.getPosts()
  }
};
</script>
