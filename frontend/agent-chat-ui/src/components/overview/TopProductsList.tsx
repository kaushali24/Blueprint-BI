import { ProductMetricItemDTO } from "@/lib/api/types";

interface TopProductsListProps {
  products: ProductMetricItemDTO[];
}

export default function TopProductsList({ products }: TopProductsListProps) {
  if (products.length === 0) {
    return (
      <section className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-gap-md h-full">
        <h3 className="headline-md text-ci-on-surface">Top Products</h3>
        <p className="body-md text-ci-secondary">No products sold yet.</p>
      </section>
    );
  }

  const displayProducts = products.slice(0, 5);
  const featuredProduct = displayProducts[0];
  const supportingProducts = displayProducts.slice(1);

  return (
    <section className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-gap-md h-full">
      <div className="flex flex-col gap-1">
        <h3 className="headline-md text-ci-on-surface">Top Products</h3>
        <span className="body-sm text-ci-secondary">By confirmed quantity</span>
      </div>

      <div className="flex flex-col gap-2 flex-1">
        <div className="bg-ci-surface-container border border-ci-surface-variant rounded-xl p-4 flex flex-col gap-1.5 mt-1">
          <span className="label-caps text-ci-primary uppercase">Top Product</span>
          <div className="flex items-start justify-between gap-3 min-w-0 mt-1">
            <span className="text-lg font-semibold text-ci-on-surface break-words min-w-0 leading-tight">{featuredProduct.product_name}</span>
            <span className="text-lg font-bold text-ci-on-surface shrink-0">{parseFloat(featuredProduct.total_quantity).toString()}</span>
          </div>
          <span className="body-sm text-ci-secondary mt-1">Highest confirmed quantity</span>
        </div>

        {supportingProducts.length > 0 && (
          <ul className="flex flex-col mt-2">
            {supportingProducts.map((product, index) => {
              const qty = parseFloat(product.total_quantity);
              return (
                <li key={index} className="flex items-center justify-between gap-4 py-3 border-b border-ci-surface-variant last:border-0 min-w-0">
                  <span className="body-md text-ci-on-surface truncate min-w-0" title={product.product_name}>{product.product_name}</span>
                  <span className="body-md font-medium text-ci-secondary shrink-0">{qty.toString()}</span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
