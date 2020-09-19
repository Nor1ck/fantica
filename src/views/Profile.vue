<template>
  <div class="home">
    <p v-if="profile.username !== null">{{metamaskAddress}}</p>
    <div v-if="profile.username !== null">
        <img src="../assets/cover.png" width="400" alt="cover" @click="uploadCoverImage()" />
        <br>
        <img src="../assets/test_pic.jpg" width="100" alt="profile photo" @click="uploadProfilePhoto()" />
        <v-row justify="center">
        <v-col cols="12" sm="6" md="3">
            <v-switch @click="setSubscriptionAccess()" :loading="switchIsLoading" v-model="subscriptionAccessPaid" :label="`Subscription Access: ${subscriptionAccessPaid == 1 ? 'Paid' : 'Free' }`"></v-switch>
            <div v-if="subscriptionAccessPaid">
                <v-row>
                    <v-col cols="6">
                        <v-text-field v-model="monthlyPrice" prefix="$" type="number" label="Montly Price"></v-text-field>
                    </v-col>
                    <v-col cols="6">
                        <v-text-field v-model="annualPrice" prefix="$" type="number" label="Annual Price"></v-text-field>
                    </v-col>
                </v-row>
                <v-btn :loading="setIsLoading" outlined rounded small color="indigo" @click="setSubscriptionPrice()">Set</v-btn>
            </div>

            <v-text-field v-model="profile.username" label="@username"></v-text-field>
            <v-text-field v-model="profile.displayname" label="Display name"></v-text-field>
            <v-text-field v-model="profile.about" label="About"></v-text-field>
            <v-text-field v-model="profile.location" label="Location"></v-text-field>
            <v-text-field v-model="profile.website" label="Website"></v-text-field>
            <v-btn :loading="saveChangesIsLoading" outlined rounded color="primary" @click="updateProfile()">Save changes</v-btn>
        </v-col>
        </v-row>
    </div>
  </div>
</template>

<script>
export default {
  name: "Profile",
  components: {},
  data() {
    return {
        subscriptionAccessPaid: false,
        saveChangesIsLoading: false,
        switchIsLoading: false,
        setIsLoading: false,
        monthlyPrice: 0,
        annualPrice: 0,
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
    gasPrice() {
      return this.$store.state.gasPrice;
    },
  },
  methods: {
    async updateProfile() {
      this.saveChangesIsLoading = true;
      try {
        await this.$http.post(this.$HOST + '/api/update_profile', JSON.stringify(this.profile), { withCredentials: true });
      } finally {
        this.saveChangesIsLoading = false;
      }
    },
    async subscriptionPrice() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let monthlyPrice = await contract.methods.subscriptionPrice(this.metamaskAddress, 1).call();
      let annualPrice = await contract.methods.subscriptionPrice(this.metamaskAddress, 2).call();
      this.monthlyPrice = Number(window.web3.utils.fromWei(monthlyPrice, 'ether')).toFixed(2)
      this.annualPrice = Number(window.web3.utils.fromWei(annualPrice, 'ether')).toFixed(2)
    },
    async subscriptionAccessIsFree() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      this.subscriptionAccessPaid = !await contract.methods.subscriptionAccessIsFree(this.metamaskAddress).call();
    },
    async setSubscriptionPrice() {
      this.setIsLoading = true;
      try {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress,
          { from: this.metamaskAddress }
        );
        let monthlyPrice = window.web3.utils.toWei(this.monthlyPrice, 'ether');
        let annualPrice = window.web3.utils.toWei(this.annualPrice, 'ether');
        await contract.methods.setSubscriptionPrice(monthlyPrice, annualPrice).send();
      } finally {
        this.setIsLoading = false;
      }
    },
    async setSubscriptionAccess() {
      this.switchIsLoading = true;
      try {
        let contract = new window.web3.eth.Contract(
          this.fanticaDAppABI,
          this.fanticaDAppAddress,
          { from: this.metamaskAddress }
        );
        await contract.methods.setSubscriptionAccess(!this.subscriptionAccessPaid).send();
      } catch {
        this.subscriptionAccessPaid = !this.subscriptionAccessPaid;
      } finally {
        this.switchIsLoading = false;
      }
      if (this.subscriptionAccessPaid) {
        this.subscriptionPrice();
      }
    },
    uploadCoverImage() {},
    uploadProfilePhoto() {},
    // async send() {
    //   let contract = new window.web3.eth.Contract(
    //     this.contractABI,
    //     this.tokenAddress,
    //     { from: this.metamaskAddress }
    //   );
    //   let v = await contract.methods
    //     .transfer(this.recipient, window.web3.utils.toWei(this.recipientAmount))
    //     .send({ gasPrice: this.gasPrice.toString() });
    //   console.log(v);
    // }
  },
  mounted() {
    this.subscriptionPrice();
    this.subscriptionAccessIsFree();
  }
};
</script>
