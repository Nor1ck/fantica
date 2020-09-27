
<template>
  <v-row justify="center">
    <v-dialog v-model="show" persistent max-width="290">
      <v-card>
        <v-card-title class="headline">Select period</v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-radio-group v-model="period" :mandatory="false">
            <v-radio :label="'Monthly $' + monthlyPrice" value="1"></v-radio>
            <v-radio :label="'Annual $' + annualPrice" value="2"></v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="callback(false)">Cancel</v-btn>
          <v-btn color="primary" text @click="callback(true, period)">Subscribe</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script>
export default {
  data: () => ({
    period: '1',
    dialog: true,
    monthlyPrice: '',
    annualPrice: '',
  }),
  props: {
    show: Boolean,
    callback: Function,
    address: String,
  },
  computed: {
    fanticaDAppAddress() {
      return this.$store.state.fanticaDAppAddress;
    },
    fanticaDAppABI() {
      return this.$store.state.fanticaDAppABI;
    },
  },
  methods: {
    async getSubscriptionPrice() {
      let contract = new window.web3.eth.Contract(
        this.fanticaDAppABI,
        this.fanticaDAppAddress
      );
      let monthlyPrice = await contract.methods.subscriptionPrice(this.address, 1).call();
      let annualPrice = await contract.methods.subscriptionPrice(this.address, 2).call();
      this.monthlyPrice = Number(window.web3.utils.fromWei(monthlyPrice, 'ether')).toFixed(2)
      this.annualPrice = Number(window.web3.utils.fromWei(annualPrice, 'ether')).toFixed(2)
    },
  },
  mounted() {
    this.getSubscriptionPrice();
  },
};
</script>