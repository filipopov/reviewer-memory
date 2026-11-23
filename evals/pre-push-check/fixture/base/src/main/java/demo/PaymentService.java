package demo;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.Instant;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PaymentService {

  private static final Logger LOG = LoggerFactory.getLogger(PaymentService.class);

  private final PaymentRepository repository;
  private final Clock clock;

  public PaymentService(PaymentRepository repository, Clock clock) {
    this.repository = repository;
    this.clock = clock;
  }

  public Payment create(PaymentRequest request) {
    Payment payment = new Payment(UUID.randomUUID().toString(), request.amount(), Instant.now(clock));
    repository.save(payment);
    LOG.info("Created payment {}", payment.id());
    return payment;
  }

  public record Payment(String id, BigDecimal amount, Instant createdAt) {
  }

  public interface PaymentRepository {
    void save(Payment payment);
  }
}
