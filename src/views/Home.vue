<template>
  <div class="home">
    <h1>Fantica Home</h1>

    <p>
      Fantica DApp: <a :href="fanticaDAppURL" target="_blank">{{ fanticaDAppAddress }}</a>
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
