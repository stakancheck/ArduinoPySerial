void setup() {
  Serial.begin(9600);
}

void loop() {
  for (int i = 0; i < 256; i++) {
    Serial.println(String(i) + "*" + String(255 - i) + "*" + String(i * 4));
  }
}
