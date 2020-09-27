<template>
  <div class="wallet">
    <h1>Wallet</h1>
    <v-btn v-if="daiAllowance == 0" @click="approveDAIForDApp()" rounded color="primary">Approve DAI for Fantica DApp</v-btn>
    <p>Availabe DAI: {{ balance }}</p>
    <v-btn v-if="balance > 0" rounded color="purple accent-1" @click="withdrawDAI()">Withdraw DAI</v-btn>

    <p class="mt-5" v-if="isOwner">Availabe DAI Fees: {{ feesBalance }}</p>
    <v-btn v-if="feesBalance > 0" rounded color="yellow accent-1" @click="withdrawDAIFees()">Withdraw DAI Fees</v-btn>

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
      balance: '0.00',
      feesBalance: '0.00',
      isOwner: false,
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
    daiABI() {
      return this.$store.state.daiABI;
    },
    DAIAddress() {
      return this.$store.state.DAIAddress;
    },
    daiAllowance() {
      return this.$store.state.daiAllowance;
    },
  },
  methods: {
    buyFNT() {

    },
    buyDAI() {

    },
    async getOwner() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let owner = await contract.methods.owner().call();
      this.isOwner = owner == this.metamaskAddress;
      if (this.isOwner) {
        this.daiBalanceFees();
      }
    },
    async daiBalance() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let balance = await contract.methods.balanceOfDAI(this.metamaskAddress).call();
      this.balance = Number(window.web3.utils.fromWei(balance, 'ether')).toFixed(2)
    },
    async daiBalanceFees() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let feesBalance = await contract.methods.balanceOfDAI(this.fanticaDAppAddress).call();
      this.feesBalance = Number(window.web3.utils.fromWei(feesBalance, 'ether')).toFixed(2)
    },
    async withdrawDAI() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.withdrawDAI().send();
    },
    async withdrawDAIFees() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.withdrawDAIFees().send();
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
  },
  mounted() {
    this.daiBalance();
    this.getOwner();
  }
};
</script>
