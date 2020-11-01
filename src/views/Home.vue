<template>
  <div class="home">
    <h1>Fantica Home</h1>

    <p>
      Fantica DApp:
      <a :href="fanticaDAppURL" target="_blank">{{ fanticaDAppAddress }}</a>
    </p>

    <p>
      <a
        href="https://info.uniswap.org/token/0x3d23f2e86a9ab43561203b143c18ad9de0b5c745"
        target="_blank"
        >Uniswap Fantica (FNT) Info</a
      >
    </p>
    <p>
      <a
        href="https://uniswap.info/pair/0xcf35b2923cf8cc152846194592b69a08180cdaea"
        target="_blank"
        >Uniswap FNT-ETH Pair</a
      >
    </p>
    <p>
      <a
        href="https://etherscan.io/address/0x3d23f2e86a9ab43561203b143c18ad9de0b5c745#code"
        target="_blank"
        >Fantica ERC-20 Contract</a
      >
    </p>

    <!-- <v-btn rounded color="purple accent-1" @click="buyFNT()">Buy FNT</v-btn>
    <v-btn rounded color="yellow darken-1" @click="buyFNT()">Buy DAI</v-btn> -->
  </div>
</template>

<script>
export default {
  name: "Home",
  components: {},
  data() {
    return {};
  },
  computed: {
    fanticaDAppAddress() {
      return this.$store.state.fanticaDAppAddress;
    },
    fanticaDAppURL() {
      return "https://kovan.etherscan.io/address/" + this.fanticaDAppAddress; // TODO change to mainnet
    },
  },
  methods: {
    buyFNT() {},
    buyDAI() {},
  },
};
</script>
