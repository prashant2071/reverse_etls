with survival_data as (
	SELECT sex,count(*) as count 
    from {{source("titanic_source","titanic")}}
group by sex
)

select sex,
	count(*) as survived,
	case 
	when sex = 'male' then Round(count(*)*100.0/(select count from survival_data where sex= 'male' ),2) 
	when sex = 'female' then Round(count(*)*100.0/(select count from survival_data where sex= 'female' ),2) end as survived_percentage

from {{source("titanic_source","titanic")}}
		where survived = 1
group by sex

