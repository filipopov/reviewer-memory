package demo;

import java.math.BigDecimal;

public record PaymentRequest(String debtorName, String debtorIban, String creditorIban, BigDecimal amount) {
}
