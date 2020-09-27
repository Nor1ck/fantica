
<template>
  <v-row justify="center">
    <v-dialog v-model="show" persistent max-width="290">
      <v-card>
        <v-card-title class="headline">Tips</v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-row>
              <v-col cols="12">
                <v-text-field v-model="amount" label="Amount*" required type="number"></v-text-field>
              </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="callback(false)">Cancel</v-btn>
          <v-btn color="primary" text @click="callback(true, amount)">Send</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script>
export default {
  data: () => ({
    amount: 10,
    dialog: true,
  }),
  props: {
    show: Boolean,
    callback: Function,
  },
};
</script>