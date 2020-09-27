<template>
  <v-app>
    <v-main>
      <div id="nav">
        <router-link to="/">Home</router-link> |
        <router-link to="/feed">Feed</router-link> |
        <span v-if="!profile.username" @click="auth()" tag="button" class="btn">Log in</span>
        <span v-else>
          <router-link :to="{ name: 'UserPage', params: {address: metamaskAddress} }">Me</router-link>
          | <router-link to="/profile">Profile</router-link>
          | <router-link to="/wallet">Wallet</router-link>
          | <router-link to="/newpost">New Post</router-link>
          | <span @click="logOut()" tag="button" class="btn">Log Out</span>
        </span>
      </div>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
var Web3 = require("web3");

export default {
  name: "Home",
  data() {
    return {};
  },
  watch: {
    metamaskAddress(newValue) {
      console.log('metamask ' + newValue);
      if (this.$cookie.get('address') && newValue != this.$cookie.get('address')) {
        this.logOut()
      }
      this.daiAllowanceForDApp()
    }
  },
  computed: {
    metamaskAddress() {
      return this.$store.state.metamaskAddress
    },
    fanticaDAppAddress() {
      return this.$store.state.fanticaDAppAddress
    },
    profile() {
      return this.$store.state.profile;
    },
    daiABI() {
      return this.$store.state.daiABI;
    },
    DAIAddress() {
      return this.$store.state.DAIAddress;
    },
  },
  methods: {
    async auth() {
      if (this.metamaskAddress) {
        let message = 'Address: ' + this.metamaskAddress;
        let signature = await window.web3.eth.personal.sign(message, this.metamaskAddress);
        if (signature) {
          let resp = await this.$http.post(this.$HOST + '/api/auth', JSON.stringify({msg: message, sign: signature}), { withCredentials: true });
          if (resp.status == 200) {
            this.$cookie.set('token', resp.data.token, resp.data.expires);
            this.$cookie.set('address', this.metamaskAddress, resp.data.expires);
            await this.getProfile();
            this.$router.push('/profile')
          }
        }
      }
    },
    logOut() {
      this.$cookie.delete('token');
        this.$cookie.delete('address');
        this.$store.commit('setToken', null);
        this.$store.commit('resetProfile');
        this.$router.push('/')
    },
    goNewPost() {
      this.$router.push('/newpost');
    },
    connectToMetamask() {
      if (window.ethereum) {
        window.ethereum.autoRefreshOnNetworkChange = false;
        window.web3 = new Web3(window.ethereum);
        window.ethereum.send("eth_requestAccounts");
        if (window.ethereum.selectedAddress) {
          this.$store.commit(
            "setMetamaskAddress",
            window.web3.utils.toChecksumAddress(window.ethereum.selectedAddress)
          );
        }
        var _this = this;
        window.ethereum.on("accountsChanged", async (accounts) => {
          _this.$store.commit("setMetamaskAddress", window.web3.utils.toChecksumAddress(accounts[0]));
        });
        window.ethereum.on("chainChanged", async (networkId) => {
          _this.$store.commit("setEthNetwork", networkId);
        });
        this.$store.commit("setEthNetwork", window.ethereum.networkVersion);
        return true;
      }
      return false;
    },
    async getGasPrice() {
      window.web3.eth.getGasPrice((err, gasPrice) => {
        err ? console.log(err) : this.$store.commit('setGasPrice', window.web3.utils.fromWei(gasPrice, "gwei"))
      });
    },
    async getMetamaskBalance() {
      window.web3.eth.getBalance(this.metamaskAddress, (err, balance) => {
        this.metamaskBalance = window.web3.utils.fromWei(balance, "ether");
      });
    },
    async getProfile() {
      if (this.$cookie.get("token")) {
        let resp = await this.$http.post(this.$HOST + '/api/profile', {}, { withCredentials: true });
        if (resp.status == 200) {
          this.$store.commit('setProfile', resp.data.profile);
        }
      }
    },
    readCookie() {
      if (this.$cookie.get("token")) {
        this.$store.commit('setToken', this.$cookie.get("token"))
      }
    },
    async daiAllowanceForDApp() {
      let contract = new window.web3.eth.Contract(
        this.daiABI,
        this.DAIAddress
      );
      let daiAllowance = await contract.methods.allowance(this.metamaskAddress, this.fanticaDAppAddress).call();
      this.$store.commit('setDaiAllowance', daiAllowance);
    },
  },
  mounted() {
    this.connectToMetamask();
    this.getProfile();
    this.getGasPrice();
  },
  destroyed() {
    console.log('destroyed');
  }
};
</script>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

#nav {
  padding: 20px;

  a {
    font-weight: bold;
    color: #2c3e50;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
.btn {
  font-weight: bold;
  color: #2c3e50;
  cursor: pointer;
  text-decoration: underline;
}
.btn:focus {
  outline: none;
}
</style>
