<template>
  <div class="wallet">
    <h1>Wallet</h1>
    <p>Availabe DAI: {{ balance }}</p>
    <v-btn v-if="balance > 0" rounded color="purple accent-1" @click="withdrawDAI()">Withdraw</v-btn>
    <p class="mt-5">TODO: Show Transactions</p>
    <!-- <v-btn rounded color="yellow darken-1" @click="buyFNT()">Buy DAI</v-btn> -->
  </div>
</template>

<script>

export default {
  name: "Wallet",
  components: {
  },
  data() {
    return {
      balance: 0,
    };
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
    buyFNT() {

    },
    buyDAI() {

    },
    async daiBalance() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let balance = await contract.methods.balanceOfDAI(this.metamaskAddress).call();
      this.balance = Number(window.web3.utils.fromWei(balance, 'ether')).toFixed(2)
    },
    async withdrawDAI() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.withdrawDAI().send();
    },
  },
  mounted() {
    this.daiBalance();
  }
};
</script>
