from pprint import pprint
class Costing(object):
	# wp = writes per
	wp_customer = 100
	wp_business = 60
	wp_deal = 200
	wp_deal_shard = 5
	
	# cp = cost per
	cp_read  = 0.07/100000.
	cp_write = 0.10/100000.
	cp_small = 0.01/100000.
	
	
	deals_per_geohash ={
					5:50,
					6:10
					}
	
		
	def _cp_search(self,ghash_size=5):
		deals_per_ghash = 50
		num_ghashes = 9
		
		if ghash_size == 6:
			deals_per_ghash = 10
			num_ghashes = 49
		
		# cost per ghash search
		# cost for query
		cp_ghash = self.read(1) + self.cp_small * deals_per_ghash
		# cost for fetching
		cp_ghash += self.read(1)* deals_per_ghash
		cost_of_searching_ghashes = cp_ghash * num_ghashes
		cp_search = cost_of_searching_ghashes
		
		
		
		# cost for shard reading/writing
		num_deals = num_ghashes * deals_per_ghash
		# read write for one shard for each deal
		# cp_deal
		cost_of_counting = self.read(num_deals) +self.deal_shard_write(num_deals)
		cp_search += cost_of_counting
		
		# pull customer in beginning
		cp_search += self.read(1)
		
		return cp_search
	def searches(self,dau):
		'''
		This is cost per day
		'''
		searches_per_customer = 5
		cp_search = self._cp_search(5)
		
		cost_of_search = cp_search * searches_per_customer * dau
		return cost_of_search # per day
	
	def read(self,n):
		return self.cp_read*n
	def deal_write(self,n):
		return self.cp_write*self.wp_deal*n
	def customer_write(self,n):
		return self.cp_write*self.wp_customer*n
	
	def login(self,n):
		'''
		@return: cost of n logins
		'''
		
	
	def img_view(self,n):
		'''
		1 deal read
		1 blob read
		= 2x read
		@return: cost of n img views
		'''
		reads_per_view = 2
		reads = reads_per_view * n
		return self.c_read(reads)
	
		
def main():
	daus = [1000,10000,100000,1000000]
	costing = Costing()
	cost_of_searches = [costing.searches(dau) for dau in daus]
	pprint(cost_of_searches)
	
if __name__ == '__main__':
	main()