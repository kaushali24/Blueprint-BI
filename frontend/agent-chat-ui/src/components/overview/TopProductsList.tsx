import { ProductMetricItemDTO } from "@/lib/api/types";

interface TopProductsListProps {
  products: ProductMetricItemDTO[];
}

export default function TopProductsList({ products }: TopProductsListProps) {
  if (products.length === 0) {
    return (
      <section className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-gap-md">
        <h3 className="headline-md text-ci-on-surface">Top Products</h3>
        <p className="body-md text-ci-secondary">No products sold yet.</p>
      </section>
    );
  }

  return (
    <section className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-gap-md">
      <h3 className="headline-md text-ci-on-surface">Top Products</h3>
      <ul className="flex flex-col gap-3">
        {products.map((product, index) => (
          <li key={index} className="flex items-center justify-between gap-3 py-4 border-b border-ci-surface-variant last:border-0 min-w-0">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <span className="label-caps text-ci-secondary w-4 shrink-0">{index + 1}.</span>
              <span className="body-md text-ci-on-surface font-semibold break-words min-w-0">{product.product_name}</span>
            </div>
            <span className="metadata text-ci-secondary shrink-0">{parseFloat(product.total_quantity).toString()}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
