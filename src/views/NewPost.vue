<template>
  <div class="NewPost">
    <v-row justify="center">
      <v-col cols="12" sm="6" md="3">
        <v-text-field v-model="post.message" label="Message"></v-text-field>
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-col cols="12" sm="6" md="3" class="pt-0">
        <v-file-input
          multiple
          chips
          outlined
          v-model="media"
          accept="image/png, image/jpeg, image/bmp"
          placeholder="Add a media"
          prepend-icon="mdi-camera"
          label="Media">
          <template v-slot:selection="{ text }">
            <v-chip
              small
              label
              color="primary"
            >
              {{ text }}
            </v-chip>
          </template>
        ></v-file-input>
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
        'media_count': 0,
      },
      media: [],
    };
  },
  methods: {
    async createPost() {
      if (this.post.message) {
        this.loading = true;
        try {
          this.post.media_count = this.media.length;
          let resp = await this.$http.post(this.$HOST + '/api/new_post', JSON.stringify(this.post), { withCredentials: true });
          if (resp.data.secret) {
            for (let index = 0; index < this.media.length; index++) {
              const media = this.media[index];
              this.uploadMedia(resp.data.secret, index, media)
            }
          }
        } finally {
          this.loading = false;
          this.post.message = null;
          this.media = [];
        }
      }
    },
    async uploadMedia(secret, index, media) {
      var formData = new FormData();
      formData.append("image", media);
      await this.$http.post(this.$HOST + '/api/upload/media/' + secret + '/' + index, formData, {
          withCredentials: true,
          headers: {
            'Content-Type': 'multipart/form-data'
          }
      });
    },
  },
};
</script>

<style scoped>
.pt-0 {
    padding-top: 0!important;
}
</style>
