package demo;

public class PaymentController {

  private final PaymentService service;

  public PaymentController(PaymentService service) {
    this.service = service;
  }

  public PaymentService.Payment create(PaymentRequest request) {
    if (request.amount().signum() <= 0) {
      throw new IllegalArgumentException("amount must be positive");
    }
    return service.create(request);
  }
}
