<template>
<div>
  <v-row justify="center">
    <v-col cols="12" sm="12" md="6">

      <v-card class="mx-auto">
        <v-img src="https://cdn.vuetifyjs.com/images/cards/sunshine.jpg" height="200px"></v-img>

        <v-card-title>
          <v-list-item class="grow">
            <v-list-item-avatar color="grey darken-3">
              <v-img
                class="elevation-6"
                :src="avatarURL"
              ></v-img>
            </v-list-item-avatar>

            <v-list-item-content>
              <router-link class="ta-l" :to="{ name: 'UserPage', params: {address: post.address} }">{{post.username}}</router-link>
            </v-list-item-content>
          </v-list-item>
        </v-card-title>

        <v-card-subtitle class="card-text ta-l">{{post.message}}</v-card-subtitle>

        <v-card-actions v-if="post.address != metamaskAddress">
          <v-btn color="primary" text @click="purchase()">Buy for</v-btn>
          <v-btn color="primary" text @click="showSubscribe = true">Subscribe</v-btn>
          <v-btn color="primary" text @click="showTips = true">Send Tips</v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text @click="showDelete = true">Delete</v-btn>
        </v-card-actions>
      </v-card>

    </v-col>
  </v-row>

  <DialogYesNo :show="showDelete" :callback="deletePost"/>
  <DialogSelect :show="showSubscribe" :callback="subscribe"/>
  <DialogInput :show="showTips" :callback="sendTips"/>
</div>

</template>

<script>
import DialogYesNo from "@/components/dialogs/DialogYesNo.vue";
import DialogSelect from "@/components/dialogs/DialogSelect.vue";
import DialogInput from "@/components/dialogs/DialogInput.vue";

export default {
  components: {
    DialogYesNo,
    DialogSelect,
    DialogInput,
  },
  props: {
    post: Object,
    username: String,
  },
  data() {
    return {
      showDelete: false,
      showSubscribe: false,
      showTips: false,
      avatarURL: null,
    }
  },
  computed: {
    metamaskAddress() {
      return this.$store.state.metamaskAddress;
    },
    DAIAddress() {
      return this.$store.state.DAIAddress;
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
    daiAllowance() {
      return this.$store.state.fanticaDAppABI;
    },
  },
  methods: {
    async subscribe(result, period) {
      this.showSubscribe = false;
      if (!result) return
      let creator = this.post._id.split(":")[0];
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.subscribe(creator, period).send();
    },
    async purchase() {
      let creator = this.post._id.split(":")[0];
      let contentId = this.post._id.split(":")[1];
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.purchase(creator, contentId).send();
    },
    async sendTips(result, amount) {
      this.showTips = false;
      if (!result) return
      let creator = this.post._id.split(":")[0];
      let contentId = this.post._id.split(":")[1];
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.sendTips(creator, contentId, window.web3.utils.toWei(amount, 'ether')).send();
    },
    async approveDAIForDApp() {
      let contract = new window.web3.eth.Contract(
        this.daiABI,
        this.DAIAddress,
        { from: this.metamaskAddress }
      );
      let maxUINT = '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'; // max uint 2 ** 256
      await contract.methods.approve(this.fanticaDAppAddress, maxUINT).send();
    },
    async deletePost(result) {
      this.showDelete = false;
      if (!result) return
      let resp = await this.$http.post(this.$HOST + '/api/posts/delete', JSON.stringify({post_id: this.post._id}), { withCredentials: true });
      if (resp.status == 200) {
          this.$destroy()
          this.$el.parentNode.removeChild(this.$el);
      }
    }
  },
  mounted() {
    this.avatarURL = this.$HOST + '/static/avatar/' + this.post.address + '/avatar.jpg'
  }
};
</script>

<style lang="scss">
.grow {
  padding-left: 0;
}
.ta-l {
  text-align: left !important;
}
.td-n {
  text-decoration: none;
}
</style>