package demo;

public class PaymentController {

  private final PaymentService service;

  public PaymentController(PaymentService service) {
    this.service = service;
  }

  public PaymentService.Payment create(PaymentRequest request) {
    return service.create(request);
  }
}
