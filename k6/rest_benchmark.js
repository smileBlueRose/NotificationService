import http from "k6/http";
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

function generateUuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (symbol) => {
    const random = (Math.random() * 16) | 0;
    const value = symbol === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export default function () {
  const event = {
    event_id: generateUuid(),
    event_type: "pin_liked",
    recipient_id: Math.floor(Math.random() * 1000) + 1,
    created_at: new Date().toISOString(),
    payload: { actor: "anna", pin_id: `pin-${Math.floor(Math.random() * 100000)}` },
  };
  const response = http.post(`${__ENV.URL}/v1/events`, JSON.stringify(event), {
    headers: { "Content-Type": "application/json" },
  });
  check(response, { "status is 202": (result) => result.status === 202 });
}