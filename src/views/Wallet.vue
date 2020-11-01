<template>
  <div class="wallet">
    <h1>Wallet</h1>
    <v-btn
      v-if="daiAllowance == 0"
      @click="approveDAIForDApp()"
      rounded
      color="primary"
      >Approve DAI for Fantica DApp</v-btn
    >
    <p>DAI Balance: {{ daiBalance }}</p>
    <p>Earned DAI: {{ earned }}</p>
    <v-btn
      v-if="earned > 0"
      rounded
      color="purple accent-1"
      @click="withdrawDAI()"
      >Withdraw Earned DAI</v-btn
    >

    <p class="mt-5" v-if="isOwner">Fantica DAI Fees: {{ feesEarned }}</p>
    <v-btn
      v-if="feesEarned > 0"
      rounded
      color="yellow accent-1"
      @click="withdrawDAIFees()"
      >Withdraw Fantica DAI Fees</v-btn
    >

    <h1 class="mt-5">TODO: Show Transactions</h1>
    <!-- <v-btn rounded color="yellow darken-1" @click="buyFNT()">Buy DAI</v-btn> -->
  </div>
</template>

<script>
export default {
  name: "Wallet",
  components: {},
  data() {
    return {
      daiBalance: "0.00",
      earned: "0.00",
      feesEarned: "0.00",
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
    buyFNT() {},
    buyDAI() {},
    async getOwner() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let owner = await contract.methods.owner().call();
      this.isOwner = owner == this.metamaskAddress;
      if (this.isOwner) {
        this.getDAIFees();
      }
    },
    async getDAIEarned() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let earned = await contract.methods
        .balanceOfDAI(this.metamaskAddress)
        .call();
      this.earned = Number(window.web3.utils.fromWei(earned, "ether")).toFixed(
        2
      );
    },
    async getDAIFees() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let feesEarned = await contract.methods
        .balanceOfDAI(this.fanticaDAppAddress)
        .call();
      this.feesEarned = Number(
        window.web3.utils.fromWei(feesEarned, "ether")
      ).toFixed(2);
    },
    async withdrawDAI() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.withdrawDAI().send();
      this.updateBalances();
    },
    async withdrawDAIFees() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress,
        { from: this.metamaskAddress }
      );
      await contract.methods.withdrawDAIFees().send();
      this.updateBalances();
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
    async getDAIBalance() {
      let contract = new window.web3.eth.Contract(
        this.daiABI,
        this.DAIAddress,
        { from: this.metamaskAddress }
      );
      let daiBalance = await contract.methods
        .balanceOf(this.metamaskAddress)
        .call();
      this.daiBalance = Number(
        window.web3.utils.fromWei(daiBalance, "ether")
      ).toFixed(2);
    },
    updateBalances() {
      this.getDAIBalance();
      this.getDAIEarned();
      this.getOwner();
    },
  },
  mounted() {
    this.updateBalances();
  },
};
</script>
