
<template>
  <v-row justify="center">
    <v-dialog v-model="show" persistent max-width="290">
      <v-card>
        <v-card-title class="headline">Select period</v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-radio-group v-model="period" :mandatory="false">
            <v-radio label="Monthly" value="1"></v-radio>
            <v-radio label="Annual" value="2"></v-radio>
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
  }),
  props: {
    show: Boolean,
    callback: Function,
  },
};
</script>