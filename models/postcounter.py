import datetime
from google.appengine.ext import ndb


class Month(ndb.Model):
	year = ndb.IntegerProperty()
	month = ndb.IntegerProperty(choices=(1,2,3,4,5,6,7,8,9,10,11,12))
	count = ndb.IntegerProperty()

class PostCounter(ndb.Model):
	count = ndb.IntegerProperty(indexed=False, default=0)
	months = ndb.StructuredProperty(Month, repeated=True)

	def increment(self, year, month, put=True):
		m = self._get_month(year, month)
		m.count += 1
		self.count = sum(m.count for m in self.months)
		if put:
			self.put()

	def decrement(self, year, month, put=True):
		m = self._get_month(year, month)
		m.count -= 1
		self.count = sum(m.count for m in self.months)
		if put:
			self.put()

	def _get_month(self, year, month):
		for m in self.months:
			if m.year == year and m.month == month:
				return m

		m = Month(year=year, month=month, count=0)
		self.months.append(m)
		return m


	@classmethod
 	def get(cls):
 		counter = cls.query().get()

 		if not counter:
 			counter = PostCounter(count=0)
 			counter.put()

 		return counter
