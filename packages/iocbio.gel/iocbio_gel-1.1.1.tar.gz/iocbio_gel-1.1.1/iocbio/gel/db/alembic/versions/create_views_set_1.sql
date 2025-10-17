-- Drop views if they exist in the order taking into account the dependencies
DROP VIEW IF EXISTS measurement_relative_value;
DROP VIEW IF EXISTS measurement_reference_value;

-- Create views
CREATE VIEW measurement_reference_value AS
SELECT ml.measurement_id,
       gil.image_id,
       avg(ml.value / gl.protein_weight) AS value_per_protein,
       min(ml.value / gl.protein_weight) AS value_per_protein_min,
       max(ml.value / gl.protein_weight) AS value_per_protein_max,
       count(*) AS n
FROM measurement_lane ml
JOIN image_lane gil ON ml.image_lane_id = gil.id
JOIN gel_lane gl ON gil.gel_lane_id = gl.id
WHERE ml.is_success
  AND gl.is_reference
  AND gl.protein_weight > 0
GROUP BY ml.measurement_id,
         gil.image_id;

CREATE VIEW measurement_relative_value AS
SELECT gl.id AS gel_lane_id,
       ml.id AS measurement_lane_id,
       gl.sample_id,
       gl.is_reference,
       ml.measurement_id,
       gil.image_id,
       ml.is_success,
       ml.value / gl.protein_weight / mrv.value_per_protein AS relative_value
FROM measurement_lane ml
JOIN image_lane gil ON ml.image_lane_id = gil.id
JOIN gel_lane gl ON gil.gel_lane_id = gl.id
JOIN measurement_reference_value mrv ON (mrv.measurement_id = ml.measurement_id
                                         AND mrv.image_id = gil.image_id)
WHERE gl.protein_weight > 0;
