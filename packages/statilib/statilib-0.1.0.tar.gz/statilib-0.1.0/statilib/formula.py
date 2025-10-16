from ast import List
from math import factorial


def class_limit(highest, lowest, num_of_classes): 
    return (highest - lowest) // num_of_classes

def percent(frquncy, total_frequncy):
    return (frquncy / total_frequncy) * 100

def relative_frequncy(num_of_frequncy, toatl_frequncy):
    return num_of_frequncy/ toatl_frequncy

def mid_point(h_limit,l_limit):
    return (h_limit + l_limit) / 2

# data description 

# sample mean
# where x -> the list of data
# n -> the length of the list  
def mean(x,n):
    summision_of_x = 0
    for i in x: 
        summision_of_x = summision_of_x + i
    return summision_of_x / n

def medine(data): 
    length = len(data)

    if length % 2 == 0: 
        indexs = length - 1 
        mid = data[indexs // 2]
        after_mid = data[(indexs // 2) + 1]
        result = (mid + after_mid) / 2 

        return result
    else:
        return data[length // 2]


def mid_range(highest_v,lowest_v): 
    return (highest_v + lowest_v) / 2

# where x -> the list of values 
# f -> the frequncies of each x 
# n -> the summision of the f 
def mean_for_grouped_data(x,f,n):
    sum_of_xf = 0

    for i in range(len(x)):
        sum_of_xf = sum_of_xf + (x[i] * f[i])
    
    result = sum_of_xf / n

    return result


def medine_for_grouped_data(f, cumulative_f):
    frquncy_column = [column[2] for column in f] 
    half_of_f_sum = sum(frquncy_column) / 2

    medine_class = None
    for i in range(len(f)):
        if f[i][3] >= half_of_f_sum:
            medine_class = f[i]
            break
    if medine_class is None:
        raise ValueError("No median class found.")
    
    lower_limit = medine_class[0] # 60
    class_width = medine_class[1] - medine_class[0] # 9

    result = lower_limit + (((half_of_f_sum - cumulative_f) / medine_class[2]) * class_width)

    return result 

def mod(data):
    dic = {}

    for v in data:
        if v in dic:
            dic[v] =+ 1
        else:
            dic[v] = 1
    
    mod = dic.get(0)
    for num, f in dic.items():
        if f > mod:
            mod = num

    result = [mod]
    multi_mod = dic.get(mod, None)

    if multi_mod is not None:
        result.append(multi_mod)
    
    return result
  
# measure of variation

def rnge(high,low):
    return high - low

def pop_variance(x,n):
    sample_mean = mean(x[:][1], n)
    squared_x_mean = []
    summision_of_squared_x_mean = 0

    for i in range(len(x)):
        squared_x_mean.append((x[i][1] - sample_mean) ** 2)

    for squared in squared_x_mean:
        summision_of_squared_x_mean =+ squared
    
    result = summision_of_squared_x_mean / n

    return result

def standard_deviation_pop(x,n):
    variance = pop_variance(x, n)
    result = variance ** 0.5

    return result


def sample_variance(x,n):
    sample_mean = mean(x[:][1], n)
    squared_x_mean = []
    summision_of_squared_x_mean = 0

    for xi in x:
        squared_x_mean.append((xi - sample_mean) ** 2)

    for squared in squared_x_mean:
        summision_of_squared_x_mean =+ squared
    
    result = summision_of_squared_x_mean / (n-1) 

    return result


def standard_deviation_sample(x,n):
    variance = sample_variance(x, n)
    result = variance ** 0.5

    return result

def variance_grouped(x,n):
    sample_mean = mean(x[:][3],n)
    squared_x_mean = []
    summision_of_fi_by_squared_x_mean = 0

    for i in range(len(x)): 
        squared_x_mean.append((x[i][2] - sample_mean) ** 2)

    for j in range(len(squared_x_mean)):
        summision_of_fi_by_squared_x_mean =+ x[j][1] * squared_x_mean[j]
    
    result = summision_of_fi_by_squared_x_mean / n

    return result

# cofficient of variation
def coff_of_variation_sample(x,n):
    standard_deviation = standard_deviation_sample(x, n)
    sample_mean = mean(x[:][1], n)

    result = (standard_deviation / sample_mean) * 100

    return result

def coff_of_variation_pop(x,n):
    standard_deviation = standard_deviation_pop(x, n)
    sample_mean = mean(x[:][1], n)

    result = (standard_deviation / sample_mean) * 100

    return result

def coumulative_frequncy_percentile(x, desired_rank):
    total_observations = len(x) # N 
    cumulative_frequncy_for_rank = 0 
    sorted_x = sorted(x)

    for i in sorted_x:
        if i <= desired_rank:
            cumulative_frequncy_for_rank =+ 1

    if cumulative_frequncy_for_rank > 0:
        result = (cumulative_frequncy_for_rank / total_observations) * 100

        return result
    
    else:
        return None

def percentile(x, desired_rank):
    sorted_x = sorted(x)
    num_below_desired_rank = 0
    total_obs = len(x)

    for i in sorted_x:
        if i < desired_rank:
            num_below_desired_rank =+ 1
    
    if num_below_desired_rank > 0:
        result = ((num_below_desired_rank + 0.5) / total_obs) * 100

        return result
    else:
        return None

def percentile_to_value(x,percentile,):
    total_data_num = len(x)
    result = (total_data_num * percentile) / 100

    if result is isinstance(float):
        result =+ 0.5
    
        return result
    elif result is isinstance(int):
        result = (result + (result +1)) / 2

        return result
    else:
        return None


# the standard scores (z-sores)

def z_scores_pop(value, x, n):
    sample_mean = mean(x[:][1], n)
    standard_deviation = standard_deviation_pop(x,n)

    result = (value - sample_mean) / standard_deviation

    return result 

def z_scores_sample(value, x, n):
    sample_mean = mean(x[:][1], n)
    standard_deviation = standard_deviation_sample(x,n)

    result = (value - sample_mean) / standard_deviation

    return result

# the quartiles and deciles 

def quar_of(data: list[float]):
    arragnged_data = sorted(data)
    data_len = len(data)

    if data_len % 2 == 0:
        indexs = data_len - 1 
        q2 = (arragnged_data[indexs // 2] + arragnged_data[(indexs // 2) + 1]) / 2 
        q1 = (arragnged_data[indexs // 4] + arragnged_data[(indexs // 4) + 1]) / 2
        q3 = (arragnged_data[(indexs // 4) * 3] + arragnged_data[((indexs // 4) * 3) + 1]) / 2
    else:
        indexs = data_len - 1 
        q2 = arragnged_data[indexs // 2]
        q1 = arragnged_data[indexs // 4]
        q3 = arragnged_data[(indexs // 4) * 3]

    return [q1, q2, q3] 

def outlier(data: list[float]):
    quar = quar_of(data)
    q1 = quar[0]
    q3 = quar[2]
    iqr = q3 - q1
    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr

    outlier = []
    for i in data:
        if i < lower_limit or i > upper_limit:
            outlier.append(i)

    return [lower_limit, upper_limit, outlier] 

def correlation_coefficient(data, n):
    sum_of_xy = 0 
    sum_of_x = 0 
    sum_of_y = 0 
    sum_of_x_squared = 0 
    sum_of_y_squared = 0 

    for i in range(len(data)):
        sum_of_xy =+ data[i][0] * data[i][1]
        sum_of_x =+ data[i][0]
        sum_of_y =+ data[i][1]
        sum_of_x_squared =+ data[i][0] ** 2
        sum_of_y_squared =+ data[i][1] ** 2
    
    result = (n * sum_of_xy - sum_of_x * sum_of_y) / ((n * sum_of_x_squared - sum_of_x ** 2) * (n * sum_of_y_squared - sum_of_y ** 2)) ** 0.5

    return result

# regression

def regression_line(data, n, x):
    sum_of_xy = 0 
    sum_of_x = 0 
    sum_of_y = 0 
    sum_of_x_squared = 0 
    sum_of_y_squared = 0 
    
    for i in range(len(data)):
        sum_of_xy =+ data[i][0] * data[i][1]
        sum_of_x =+ data[i][0]
        sum_of_y =+ data[i][1]
        sum_of_x_squared =+ data[i][0] ** 2
        sum_of_y_squared =+ data[i][1] ** 2

    a = (sum_of_y * sum_of_x_squared - sum_of_x * sum_of_xy) / (n * sum_of_x_squared - sum_of_x ** 2)
    b = (n * sum_of_xy - sum_of_x * sum_of_y) / (n * sum_of_x_squared - sum_of_x ** 2)

    result = a+b*x
    
    return result  

# probability

def prob(event, total_events):
    return event / total_events

# Bayes' Theorem 


def event_comp(prob_of_event, total_events):
    result = 1 - prob(prob_of_event,total_events)

    return result

def emprical_prob(event_occurences, total_experment_attepmts):
    return prob(event_occurences, total_experment_attepmts)

# matual and unmatual rules 

def mat_prob(event_a, total_events_a, event_b, total_event_b):
    result = prob(event_a,total_events_a) + prob(event_b,total_event_b)

    return result

def unmat_prob(event_a, total_events_a, event_b, total_event_b):
    result = (prob(event_a,total_events_a) + prob(event_b,total_event_b)) - (prob(event_a,total_events_a) * prob(event_b,total_event_b))

    return result 

# conditional probiality 

def Bayes_prob(prob_a,total_events_a,prob_b,total_events_b):
    p_b_given_a = (prob(prob_a,total_events_a) * prob(prob_b,total_events_b)) / prob(prob_a,total_events_a)
    result = (p_b_given_a * prob(prob_a,total_events_a)) / prob(prob_b,total_events_b)

    return result

def independ_intersect_prob(prob_a, total_events_a,prob_b, total_events_b):
    result = prob(prob_a, total_events_a) * prob(prob_b, total_events_b)

    return result

def depend_intersect_prob(prob_a, total_events_a,prob_b, total_events_b):
    prob_a = prob(prob_a, total_events_a)
    prob_b_given_a = independ_intersect_prob(prob_a, total_events_a, prob_b, total_events_b) / prob(prob_a, total_events_a)

    result = prob_a * prob_b_given_a

    return result 


# counting rules 

def fund_count(ways:List):
    result = 0
    for i in range(len(ways) - 2):
        result =+ (ways[i] * ways[i+1])
    
    return result

def permu_count(r,n):
    result = 0 
    fact_n = factorial(n)
    fact_n_r = factorial(n-r)

    result = fact_n / fact_n_r

    return result

def comb_count(n,r):
    result = 0 
    fact_n = factorial(n)
    fact_n_r = factorial(n-r)
    fact_r = factorial(r)

    result = fact_n / (fact_n_r * fact_r)

    return result