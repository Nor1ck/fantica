<template>
  <div class="NewPost">
    <v-row justify="center">
      <v-col cols="12" sm="6" md="3">
        <v-text-field v-model="post.message" label="Message"></v-text-field>
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-col cols="12" sm="6" md="3" class="pt-0">
        <v-row>
          <v-col cols="12" sm="6" md="3" class="pt-0">
            <v-btn outlined small color="purple">Add media</v-btn>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
    <v-btn :loading="loading" @click="createPost()" outlined rounded color="primary">post</v-btn>
  </div>
</template>

<script>
export default {
  name: "NewPost",
  data() {
    return {
      loading: false,
      post: {
        'message': null,
        'media': [],
      }
    };
  },
  methods: {
    async createPost() {
      if (this.post.message) {
        this.loading = true;
        try {
          await this.$http.post(this.$HOST + '/api/new_post', JSON.stringify(this.post), { withCredentials: true });
        } finally {
          this.loading = false;
          this.post.message = null;
          this.post.media = [];
        }
      }
    },
  },
};
</script>

<style scoped>
.pt-0 {
    padding-top: 0!important;
}
</style>
