package demo;

import java.math.BigDecimal;
import java.time.DayOfWeek;
import java.time.Instant;
import java.time.ZoneOffset;

/** Fee for a payment: 0.2 % of the amount, doubled on weekends. */
public class FeeCalculator {

  private static final double RATE = 0.002;

  public double feeFor(BigDecimal amount) {
    double fee = amount.doubleValue() * RATE;
    DayOfWeek today = Instant.now().atZone(ZoneOffset.UTC).getDayOfWeek();
    if (today == DayOfWeek.SATURDAY || today == DayOfWeek.SUNDAY) {
      fee = fee * 2;
    }
    return fee;
  }
}
