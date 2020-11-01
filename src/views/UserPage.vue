<template>
  <div>
    <img class="bgs-c" :src="coverURL" width="100%" alt="cover" />
    <div v-if="profile.about">About me: {{ profile.about }}</div>
    <div v-if="profile.location">Location: {{ profile.location }}</div>
    <div v-if="profile.website">
      Website:<a :href="profile.website" target="_blank">
        {{ profile.website }}</a
      >
    </div>
    <div v-if="!isMe() && !subscriptionAccessIsFree">
      <v-btn
        v-if="subscriptionPeriod == 0"
        color="primary"
        @click="showSubscribe = true"
        >Subscribe</v-btn
      >
      <v-btn
        v-if="
          subscriptionIsExpired() &&
          subExpiredTimestamp != -1 &&
          subscriptionPeriod > 0
        "
        color="light-blue lighten-1 white--text"
        @click="renewSubscription"
        >Renew</v-btn
      >
      <v-btn
        @click="switchSubscription()"
        color="primary"
        v-if="getAvailablePeriodName() != ''"
        class="ml-2"
        >switch to {{ getAvailablePeriodName() }}</v-btn
      >
      <v-btn
        @click="cancelSubscription()"
        v-if="subscriptionPeriod > 0"
        class="ml-2"
        color="grey lighten-5"
        >cancel subscription</v-btn
      >
    </div>
    <Post v-for="post in posts" :post="post" :key="post._id" class="mb-5" />

    <SelectPeriod
      :address="pageAddress"
      :show="showSubscribe"
      :callback="subscribe"
    />
  </div>
</template>

<script>
import moment from "moment";
import Post from "@/components/Post.vue";
import SelectPeriod from "@/components/dialogs/SelectPeriod.vue";

export default {
  name: "UserPage",
  components: {
    Post,
    SelectPeriod,
  },
  data() {
    return {
      pageAddress: null,
      subExpiredTimestamp: -1,
      showSubscribe: false,
      posts: [],
      coverURL: null,
      profile: {},
      subscriptionPeriod: 0,
      subscriptionAccessIsFree: true,
    };
  },
  watch: {
    $route() {
      this.pageAddress = this.$route.params.address;
      this.posts = [];
      this.updatePage();
    },
  },
  computed: {
    metamaskAddress() {
      return this.$store.state.metamaskAddress;
    },
    fanticaDAppAddress() {
      return this.$store.state.fanticaDAppAddress;
    },
    fanticaDAppABI() {
      return this.$store.state.fanticaDAppABI;
    },
  },
  methods: {
    isMe() {
      return this.metamaskAddress == this.pageAddress;
    },
    subscriptionIsExpired() {
      return Math.round(Number(moment.utc()) / 1000) > this.subExpiredTimestamp;
    },
    async subscribe(result, period) {
      this.showSubscribe = false;
      if (!result) return;
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.subscribe(this.pageAddress, period).send();
      this.updatePage();
    },
    async renewSubscription(result) {
      this.showSubscribe = false;
      if (!result) return;
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods
        .renewSubscription(this.metamaskAddress, this.pageAddress)
        .send();
      this.updatePage();
    },
    async getSubscriptionExpiresTs() {
      if (this.metamaskAddress != this.pageAddress) {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress
        );
        this.subExpiredTimestamp = await contract.methods
          .subscriptionExpires(this.metamaskAddress, this.pageAddress)
          .call();
      }
    },
    getAvailablePeriodName() {
      if (this.subscriptionPeriod == 1) {
        return "Annual";
      } else if (this.subscriptionPeriod == 2) {
        return "Monthly";
      }
      return "";
    },
    getAvailablePeriodValue() {
      if (this.subscriptionPeriod == 1) {
        return 2;
      } else if (this.subscriptionPeriod == 2) {
        return 1;
      }
    },
    async switchSubscription() {
      if (!this.isMe()) {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress,
          { from: this.metamaskAddress }
        );
        let period = this.getAvailablePeriodValue();
        if (period == 1) {
          await contract.methods
            .switchSubscriptionToMonthly(this.pageAddress)
            .send();
        } else if (period == 2) {
          await contract.methods
            .switchSubscriptionToAnnual(this.pageAddress)
            .send();
        } else {
          return;
        }
        this.updatePage();
      }
    },
    async cancelSubscription() {
      if (!this.isMe()) {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress,
          { from: this.metamaskAddress }
        );
        await contract.methods.cancelSubscription(this.pageAddress).send();
        this.updatePage();
      }
    },
    async getSubscriptionPeriod() {
      if (!this.isMe()) {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress
        );
        this.subscriptionPeriod = await contract.methods
          .subscriptionPeriod(this.metamaskAddress, this.pageAddress)
          .call();
      }
    },
    async getSubscriptionAccessIsFree() {
      if (!this.isMe()) {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress
        );
        this.subscriptionAccessIsFree = await contract.methods
          .subscriptionAccessIsFree(this.pageAddress)
          .call();
      }
    },
    async getPosts() {
      let resp = await this.$http.get(
        this.$HOST + "/api/posts/" + this.pageAddress,
        { withCredentials: true }
      );
      if (resp.status == 200) {
        this.posts = resp.data.posts;
      }
    },
    async getProfile() {
      let resp = await this.$http.get(
        this.$HOST + "/api/profile/" + this.pageAddress,
        { withCredentials: true }
      );
      if (resp.status == 200) {
        this.profile = resp.data.profile;
      }
    },
    async approveDAIForDApp() {
      let contract = new window.web3.eth.Contract(
        this.daiABI,
        this.DAIAddress,
        { from: this.metamaskAddress }
      );
      let maxUINT =
        "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"; // max uint 2 ** 256
      await contract.methods.approve(this.fanticaDAppAddress, maxUINT).send();
    },
    updatePage() {
      this.getPosts();
      this.getProfile();
      this.getSubscriptionAccessIsFree();
      this.getSubscriptionExpiresTs();
      this.getSubscriptionPeriod();
      this.coverURL =
        this.$HOST + "/static/cover/" + this.pageAddress + "/cover.jpg";
    },
  },
  created() {
    this.pageAddress = this.$route.params.address;
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