<template>
  <div class="home">
    <p><a :href="etherscanAddress" target="_blank">{{metamaskAddress}}</a></p>
    <div v-if="profile.username !== null">
        <v-row justify="center">
        <v-col cols="12" sm="6" md="3">
          <img :src="coverURL" width="400" alt="cover"/>
          <v-row>
            <v-col cols="10">
              <v-file-input
                v-model="cover"
                accept="image/png, image/jpeg, image/bmp"
                placeholder="Pick a cover"
                prepend-icon="mdi-camera"
                label="Cover"
              ></v-file-input>
            </v-col>
            <v-col cols=2 class="mt-3">
              <v-btn :disabled="!cover" :loading="coverUploading" rounded color="primary" @click="uploadCover()">Upload</v-btn>
            </v-col>
          </v-row>

          <br>
          <img :src="avatarURL" width="100" alt="avatar" @click="uploadAvatar()" />
          <v-row>
            <v-col cols="10">
              <v-file-input
                v-model="avatar"
                accept="image/png, image/jpeg, image/bmp"
                placeholder="Pick an avatar"
                prepend-icon="mdi-camera"
                label="Avatar"
              ></v-file-input>
            </v-col>
            <v-col cols=2 class="mt-3">
              <v-btn :disabled="!avatar" :loading="avatarUploading" rounded color="primary" @click="uploadAvatar()">Upload</v-btn>
            </v-col>
          </v-row>

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

            <v-text-field v-model="profile.username" label="Display name"></v-text-field>
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
        cover: null,
        coverURL: null,
        avatar: null,
        avatarURL: null,
        coverUploading: false,
        avatarUploading: false,
        subscriptionAccessPaid: true,
        saveChangesIsLoading: false,
        switchIsLoading: false,
        setIsLoading: false,
        monthlyPrice: 0,
        annualPrice: 0,
    };
  },
  watch: {
    cover(newVal) {
      if (newVal) {
        this.coverURL = URL.createObjectURL(newVal)
      } else {
        this.coverURL = this.$HOST + '/static/cover/' + this.metamaskAddress + '/cover.jpg'
      }
    },
    avatar(newVal) {
      if (newVal) {
        this.avatarURL = URL.createObjectURL(newVal)
      } else {
        this.avatarURL = this.$HOST + '/static/avatar/' + this.metamaskAddress + '/avatar.jpg'
      }
    },
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
    etherscanAddress() {
      return "https://kovan.etherscan.io/address/" + this.metamaskAddress; // TODO change to mainnet
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
    uploadCover() {
      this.coverUploading = true;
      try {
        if (this.cover) {
          var formData = new FormData();
          formData.append("image", this.cover);
          this.$http.post(this.$HOST + '/api/upload/cover', formData, {
              withCredentials: true,
              headers: {
                'Content-Type': 'multipart/form-data'
              }
          });
        }
      } finally {
        this.coverUploading = false;
      }
    },
    uploadAvatar() {
      this.avatarUploading = true;
      try {
        if (this.avatar) {
          var formData = new FormData();
          formData.append("image", this.avatar);
          this.$http.post(this.$HOST + '/api/upload/avatar', formData, {
              withCredentials: true,
              headers: {
                'Content-Type': 'multipart/form-data'
              }
          });
        }
      } finally {
        this.avatarUploading = false;
      }
    },
  },
  mounted() {
    this.subscriptionPrice();
    this.subscriptionAccessIsFree();
    this.coverURL = this.$HOST + '/static/cover/' + this.metamaskAddress + '/cover.jpg'
    this.avatarURL = this.$HOST + '/static/avatar/' + this.metamaskAddress + '/avatar.jpg'
  }
};
</script>
