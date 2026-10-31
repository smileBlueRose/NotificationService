import grpc from "k6/net/grpc";
import { check } from "k6";

export const options = {
  scenarios: {
    load: {
      executor: "shared-iterations",
      vus: Number(__ENV.VUS),
      iterations: Number(__ENV.REQUESTS),
      maxDuration: "5m",
    },
  },
  summaryTrendStats: ["p(50)", "p(95)", "p(99)", "max"],
};

const client = new grpc.Client();
client.load(["/proto"], "event_contract/events.proto");

function generateUuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (symbol) => {
    const random = (Math.random() * 16) | 0;
    const value = symbol === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export default function () {
  if (__ITER === 0) {
    client.connect(__ENV.ADDRESS, { plaintext: true });
  }
  const event = {
    event_id: generateUuid(),
    event_type: "EVENT_TYPE_PIN_LIKED",
    recipient_id: Math.floor(Math.random() * 1000) + 1,
    created_at: new Date().toISOString(),
    payload: { actor: "anna", pin_id: `pin-${Math.floor(Math.random() * 100000)}` },
  };
  const response = client.invoke("notification.v1.EventService/AcceptEvent", event);
  check(response, { "status is OK": (result) => result.status === grpc.StatusOK });
}