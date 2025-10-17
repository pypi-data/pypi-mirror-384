-- Fetch normalized values and associated metadata
select
pwp."path" as project_path, pwp."name" as project_name, g."name" as gel_name , g.ref_time,
g."comment" as comment_gel, gl.lane,  gl.sample_id, gl.protein_weight, gl.is_reference,
gl."comment" as comment_gel_lane, i.omero_id, i.original_file, mt."name" as type_name,
ml.value as raw_value, mrv.relative_value, ml.is_success, ml."comment" as comment_measurement_lane
from gel.measurement_lane ml
join gel.measurement m on ml.measurement_id = m.id
join gel.gel_to_project gtp on gtp.gel_id = ml.gel_id
join gel.project_with_path pwp on gtp.project_id = pwp.id
join gel.image i on ml.image_id = i.id
join gel.measurement_relative_value mrv on ml.id = mrv.measurement_lane_id
join gel.measurement_reference_value mrv2 on ml.measurement_id = mrv2.measurement_id
join gel.gel_lane gl on mrv.gel_lane_id = gl.id
join gel.measurement_type mt on m.type_id = mt.id
join gel.gel g on g.id = i.gel_id
order by pwp."path", ml.gel_id, ml.measurement_id, gl.lane
